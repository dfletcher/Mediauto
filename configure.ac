#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ(2.59)
AC_INIT([mediauto], [0.0.0], [graveyhead@gmail.com])
AC_CONFIG_MACRO_DIR([m4])
AC_CONFIG_SRCDIR([gnome-monitor/main.c])
AC_CONFIG_HEADER([config.h])
AM_INIT_AUTOMAKE

# Checks for programs.
AC_PROG_CXX
AC_PROG_AWK
AC_PROG_CC
AC_PROG_CPP
AC_PROG_INSTALL
AC_PROG_LN_S
AC_PROG_MAKE_SET
AC_PROG_RANLIB

MEDIAUTO_CHECK_PROGRAM([DVDBACKUP],[dvdbackup],[DVDBackup])
MEDIAUTO_CHECK_PROGRAM([MENCODER],[mencoder],[MEncoder])
MEDIAUTO_CHECK_PROGRAM([MKISOFS],[mkisofs],[mkisofs])
MEDIAUTO_CHECK_PROGRAM([EJECT],[eject],[eject])
dnl MEDIAUTO_CHECK_PROGRAM([FAKE],[fake],[fake])

dnl echo "DVDBACKUP: ${DVDBACKUP}"
dnl echo "  MKISOFS: ${MKISOFS}"
dnl echo " MENCODER: ${MENCODER}"
dnl echo "    EJECT: ${EJECT}"
dnl echo "     FAKE: ${FAKE}"

# Checks for libraries.
# FIXME: Replace `main' with a function in `-ldvd':
AC_CHECK_LIB([dvd], [main])

# Checks for header files.
AC_HEADER_DIRENT
AC_HEADER_STDC
AC_CHECK_HEADERS([fcntl.h inttypes.h libintl.h limits.h locale.h malloc.h mntent.h netinet/in.h paths.h stdint.h stdlib.h string.h sys/ioctl.h sys/param.h sys/time.h sys/timeb.h unistd.h])

# Checks for typedefs, structures, and compiler characteristics.
AC_HEADER_STDBOOL
AC_C_CONST
AC_C_INLINE
AC_TYPE_OFF_T
AC_TYPE_SIZE_T
AC_HEADER_TIME

# Checks for library functions.
AC_FUNC_CLOSEDIR_VOID
#AM_GNU_GETTEXT
AC_FUNC_GETMNTENT
AC_PROG_GCC_TRADITIONAL
AC_FUNC_MALLOC
AC_FUNC_MEMCMP
AC_FUNC_REALLOC
AC_FUNC_STAT
AC_FUNC_VPRINTF
AC_CHECK_FUNCS([ftime getcwd getmntent gettimeofday memset mkdir setlocale strcasecmp strdup strerror strncasecmp strstr strtol])

AC_CONFIG_FILES([Makefile
                 etc/Makefile
                 etc/mediauto.conf
                 etc/dbus-1/Makefile
                 etc/dbus-1/system.d/Makefile
                 site-packages/Makefile
                 gnome-monitor/Makefile])
AC_OUTPUT

echo
echo "Configuration summary:"
echo
MEDIAUTO_SUMMARY([dvdbackup],[${DVDBACKUP}])
MEDIAUTO_SUMMARY([mkisofs],[${MKISOFS}])
MEDIAUTO_SUMMARY([mencoder],[${MENCODER}])
MEDIAUTO_SUMMARY([eject],[${EJECT}])
echo
