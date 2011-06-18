AC_DEFUN([MEDIAUTO_CHECK_PROGRAM], [
  PROGPATH=""
  ENABLED="no"
  AC_ARG_WITH([$2], [enable/disable or specify $2 path], [
    if test "X${with_$2}" = "Xyes"; then
      ENABLED="yes"
    elif test "X${with_$2}" = "Xno"; then
      ENABLED="no"
    else
      PROGPATH="${with_$2}"
      ENABLED="yes"
    fi
  ], [
    ENABLED="yes"
  ])
  if test "${ENABLED}" = "yes" -a ! -x "${PROGPATH}"; then
    AC_PATH_PROGS($1, $2)
	PROGPATH="${$1}"
    if ! test -x "${PROGPATH}"; then
      AC_MSG_WARN([$3 requested but could not find an executable program. $3 functionality disabled. If the program exists on your system, try specifying an absolute path with --with-$2=/path/to/$2"])
      ENABLED="no"
    fi
  fi
  eval $1="${PROGPATH}"
  AC_SUBST([$1],[${PROGPATH}])
  AC_SUBST([$1_ENABLED],[${ENABLED}])
])

AC_DEFUN([MEDIAUTO_SUMMARY], [
  echo -n "  - $1: "
  if test "X$2" = "X"; then
    echo "not configured"
  else
    echo "$2"
  fi
])
