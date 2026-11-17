#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:?usage: test_android_sdk_tools.sh VERSION}"
WORK="$PWD/.sdk-tools-integration"
BT="$WORK/build-tools"
REMOTE="/data/local/tmp/sdk-tools-integration"
mkdir -p "$WORK" "$BT"
unzip -q -o "dist/build-tools-$VERSION-x86_64.zip" -d "$BT"

AAPT2="$BT/$VERSION/aapt2"
AAPT="$BT/$VERSION/aapt"
AIDL="$BT/$VERSION/aidl"
ZIPALIGN="$BT/$VERSION/zipalign"
DEXDUMP="$BT/$VERSION/dexdump"
for tool in "$AAPT2" "$AAPT" "$AIDL" "$ZIPALIGN" "$DEXDUMP"; do
  test -f "$tool" || { echo "Missing executable: $tool" >&2; exit 1; }
done

ANDROID_JAR="$ANDROID_HOME/platforms/android-35/android.jar"
HOST_D8="$ANDROID_HOME/build-tools/35.0.0/d8"
HOST_APKSIGNER="$ANDROID_HOME/build-tools/35.0.0/apksigner"
test -f "$ANDROID_JAR" && test -f "$HOST_D8" && test -f "$HOST_APKSIGNER"

mkdir -p "$WORK/project/res/values" "$WORK/project/res/layout" "$WORK/project/assets" \
  "$WORK/project/src/com/example/sdktoolstest" "$WORK/project/aidl/com/example/sdktoolstest" \
  "$WORK/project/classes" "$WORK/project/dex" "$WORK/project/gen"
cat > "$WORK/project/AndroidManifest.xml" <<'EOF'
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.example.sdktoolstest">
    <uses-sdk android:minSdkVersion="23" android:targetSdkVersion="35"/>
    <application android:label="@string/app_name" android:theme="@android:style/Theme.Material.Light.NoActionBar">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>
EOF
cat > "$WORK/project/res/values/strings.xml" <<'EOF'
<resources>
    <string name="app_name">SDK Tools Integration</string>
    <string name="resource_probe">AAPT2 XML resource compiled</string>
</resources>
EOF
cat > "$WORK/project/res/values/colors.xml" <<'EOF'
<resources><color name="probe_color">#ff336699</color></resources>
EOF
cat > "$WORK/project/res/layout/activity_main.xml" <<'EOF'
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical">
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="@string/resource_probe" android:textColor="@color/probe_color"/>
</LinearLayout>
EOF
printf 'asset pipeline probe\n' > "$WORK/project/assets/pipeline.txt"
cat > "$WORK/project/src/com/example/sdktoolstest/MainActivity.java" <<'EOF'
package com.example.sdktoolstest;
import android.app.Activity;
import android.os.Bundle;
public final class MainActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        setContentView(R.layout.activity_main);
    }
}
EOF
cat > "$WORK/project/aidl/com/example/sdktoolstest/ITest.aidl" <<'EOF'
package com.example.sdktoolstest;
interface ITest { int ping(); }
EOF

KEYSTORE="$WORK/debug.keystore"
if [ ! -f "$KEYSTORE" ]; then
  keytool -genkeypair -keystore "$KEYSTORE" -storepass android -keypass android \
    -alias androiddebugkey -dname "CN=Android Debug,O=Android,C=US" \
    -keyalg RSA -keysize 2048 -validity 10000 >/dev/null 2>&1
fi

adb wait-for-device
adb shell rm -rf "$REMOTE"
adb shell mkdir -p "$REMOTE/project" "$REMOTE/out/gen" "$REMOTE/out/aidl"
adb push "$WORK/project/res" "$REMOTE/project/" >/dev/null
adb push "$WORK/project/assets" "$REMOTE/project/" >/dev/null
adb push "$WORK/project/AndroidManifest.xml" "$REMOTE/project/" >/dev/null
adb push "$WORK/project/aidl" "$REMOTE/project/" >/dev/null
adb push "$ANDROID_JAR" "$REMOTE/android.jar" >/dev/null
adb push "$AAPT2" "$REMOTE/aapt2" >/dev/null
adb push "$AAPT" "$REMOTE/aapt" >/dev/null
adb push "$AIDL" "$REMOTE/aidl-bin" >/dev/null
adb push "$ZIPALIGN" "$REMOTE/zipalign" >/dev/null
adb push "$DEXDUMP" "$REMOTE/dexdump" >/dev/null
adb shell chmod 755 "$REMOTE/aapt2" "$REMOTE/aapt" "$REMOTE/aidl-bin" "$REMOTE/zipalign" "$REMOTE/dexdump"

adb shell "$REMOTE/aapt2" version
adb shell "$REMOTE/aapt" version
adb shell "$REMOTE/aidl-bin" --help >/dev/null
adb shell "$REMOTE/aapt2" compile --dir "$REMOTE/project/res" -o "$REMOTE/out/compiled.zip"
adb shell "$REMOTE/aapt2" link -o "$REMOTE/out/resources.apk" -I "$REMOTE/android.jar" \
  --manifest "$REMOTE/project/AndroidManifest.xml" --java "$REMOTE/out/gen" \
  --min-sdk-version 23 --target-sdk-version 35 --version-code 1 --version-name 1.0 \
  --auto-add-overlay -R "$REMOTE/out/compiled.zip" --asset-dir "$REMOTE/project/assets"
adb shell "$REMOTE/aidl-bin" --lang=java -o "$REMOTE/out/aidl" \
  "$REMOTE/project/aidl/com/example/sdktoolstest/ITest.aidl"
adb pull "$REMOTE/out/resources.apk" "$WORK/resources.apk" >/dev/null
adb pull "$REMOTE/out/gen" "$WORK/project/gen" >/dev/null

javac -source 8 -target 8 -bootclasspath "$ANDROID_JAR" -d "$WORK/project/classes" \
  "$WORK/project/gen/com/example/sdktoolstest/R.java" \
  "$WORK/project/src/com/example/sdktoolstest/MainActivity.java" 2>/dev/null
"$HOST_D8" --lib "$ANDROID_JAR" --min-api 23 --output "$WORK/project/dex" "$WORK/project/classes"
adb push "$WORK/project/dex/classes.dex" "$REMOTE/out/classes.dex" >/dev/null
adb shell "$REMOTE/dexdump" -f "$REMOTE/out/classes.dex" >/dev/null

cp "$WORK/resources.apk" "$WORK/unsigned.apk"
(cd "$WORK/project/dex" && zip -q "$WORK/unsigned.apk" classes.dex)
adb push "$WORK/unsigned.apk" "$REMOTE/out/unsigned.apk" >/dev/null
adb shell "$REMOTE/zipalign" -f 4 "$REMOTE/out/unsigned.apk" "$REMOTE/out/aligned.apk"
adb shell "$REMOTE/zipalign" -c -v 4 "$REMOTE/out/aligned.apk"
adb pull "$REMOTE/out/aligned.apk" "$WORK/aligned.apk" >/dev/null
"$HOST_APKSIGNER" sign --ks "$KEYSTORE" --ks-key-alias androiddebugkey \
  --ks-pass pass:android --key-pass pass:android --out "$WORK/app.apk" "$WORK/aligned.apk"
"$HOST_APKSIGNER" verify --verbose "$WORK/app.apk"
adb install -r "$WORK/app.apk"
adb logcat -c
adb shell am force-stop com.example.sdktoolstest
adb shell am start -W -n com.example.sdktoolstest/.MainActivity
sleep 2
adb shell pidof com.example.sdktoolstest >/dev/null
if adb logcat -d -s AndroidRuntime:E | grep -q "FATAL EXCEPTION"; then
  adb logcat -d -s AndroidRuntime:E
  echo "Application crashed after launch" >&2
  exit 1
fi
echo "PASS: AAPT2 XML compile/link, generated R.java, AIDL, DEX, zipalign, APK signing, install and launch ($VERSION x86_64)"
