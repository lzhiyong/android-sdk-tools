/*
 * Android NDK host-tool compatibility implementation.
 *
 * Some platform/system/core snapshots retain calls to toggle_O_NONBLOCK()
 * while compiling out the local helper for Android-target builds. Keep the
 * exact libcutils behavior available to the standalone static libcutils.
 */
#include <fcntl.h>
#include <unistd.h>

int toggle_O_NONBLOCK(int fd) {
    const int flags = fcntl(fd, F_GETFL);
    if (flags == -1 || fcntl(fd, F_SETFL, flags ^ O_NONBLOCK) == -1) {
        close(fd);
        return -1;
    }
    return fd;
}
