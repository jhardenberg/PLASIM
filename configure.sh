#!/bin/bash

rm -f *.x most_* F90_*

# Production builds use host-specific instructions where supported
# (gfortran: -march=native or -mcpu=native, Intel: -xHost on Intel CPUs).
# Such executables may not run on older or different CPUs, e.g. cluster
# compute nodes that differ from the build host. Set MOST_ARCH_OPTS to
# replace these options, or to an empty string for a portable build:
#    MOST_ARCH_OPTS= ./configure.sh
#    MOST_ARCH_OPTS="-march=x86-64-v3" ./configure.sh

# f90_accepts <compiler> <options>: succeeds if <compiler> can compile
# and link a small program with <options>
f90_accepts() {
   FLAGDIR=`mktemp -d 2>/dev/null || echo /tmp/most_flags_$$`
   mkdir -p $FLAGDIR
   printf 'program t\nreal :: x\nx = 1.0\nprint *, x\nend program t\n' \
          > $FLAGDIR/t.f90
   $1 $2 -o $FLAGDIR/t.x $FLAGDIR/t.f90 >/dev/null 2>&1
   FLAGRC=$?
   rm -rf $FLAGDIR
   return $FLAGRC
}

# check for FORTRAN-90 compiler
# put your favourite compiler in front if you have more than one
# WARNING: Portland Group Compiler pgf is reported to be buggy

for MOST_F90 in ifort ifx gfortran xlf sunf90 nagfor f90 f95 pgf90 g95 af90 NO_F90
do
   `hash 2>/dev/null $MOST_F90`
   if [ $? = 0 ] ; then break ; fi
done

if [ $MOST_F90 != "NO_F90" ] ; then
   F90_PATH=`which $MOST_F90`
   echo "Found FORTRAN-90 compiler     at: $F90_PATH"
   ARCH_OPTS=""
   if [ $MOST_F90 = "sunf90" ] ; then
      MOST_F90_OPTS="-O3"
      DEBUG_F90_OPTS="-g -C -ftrap=common"
      echo > most_precision_options "MOST_PREC=-r8"
   elif [ $MOST_F90 = "ifx" -o $MOST_F90 = "ifort" ] ; then
      # -fp-model precise: no value-unsafe reassociation (the Intel
      # default is -fp-model fast=1), for reproducible climate runs.
      # -assume dummy_aliases: prevent compiler from assuming dummy
      # arguments never alias in memory across legacy Fortran routines.
      # -xHost adds an Intel-only processor check to the executable,
      # so it is only used on Intel CPUs.
      # On non-Intel CPUs (e.g. AMD EPYC / Ryzen), use -march=core-avx2
      # on AVX2-capable hosts for both ifort and ifx to avoid LLVM znver2
      # code-generation quirks in early ifx releases.
      MOST_F90_OPTS="-O3 -fp-model precise -assume dummy_aliases"
      DEBUG_F90_OPTS="-g -C -fpe0 -traceback"
      if grep -q GenuineIntel /proc/cpuinfo 2>/dev/null || \
         sysctl -n machdep.cpu.vendor 2>/dev/null | grep -q GenuineIntel
      then
         ARCH_OPTS="-xHost"
      elif grep -q "avx2" /proc/cpuinfo 2>/dev/null || \
           sysctl -n machdep.cpu.features 2>/dev/null | grep -q AVX2
      then
         ARCH_OPTS="-march=core-avx2"
      fi
      echo > most_precision_options "MOST_PREC=-r8"
   elif [ $MOST_F90 = "nagfor" ] ; then
      MOST_F90_OPTS="-O -kind=byte"
      DEBUG_F90_OPTS="-g -C -fpe0 -traceback -kind=byte"
   elif [ $MOST_F90 = "gfortran" ] ; then
      # get major and minor version number; since GCC 7, -dumpversion
      # may print only the major version, so prefer -dumpfullversion
      GFFULL=`gfortran -dumpfullversion 2>/dev/null || gfortran -dumpversion`
      GFFULL=`echo "$GFFULL" | head -1 | sed -e 's/.*)//' -e 's/^ *//'`
      GFMAJ=`echo "$GFFULL" | awk 'BEGIN {FS="."}{print $1+0}'`
      GFMIN=`echo "$GFFULL" | awk 'BEGIN {FS="."}{print $2+0}'`
      GFVER=`expr 100 '*' $GFMAJ + $GFMIN`
      echo "gfortran version " $GFMAJ.$GFMIN
      # Production: no -finit-real=snan (initialization costs time on
      # every call; it stays in the debug options). Floating point traps
      # are kept because they are the only NaN guard during a run.
      # -funroll-loops is value-safe and does not change results.
      # flags for gfortran version >= 4.9 [ -ffpe-summary ]
      if [ "$GFVER" -ge "409" ] ; then
         MOST_F90_OPTS="-O3 -funroll-loops -ffpe-trap=invalid,zero,overflow -ffpe-summary=none"
         DEBUG_F90_OPTS="-g -O0 -ffpe-trap=invalid,zero,overflow -ffpe-summary=none -fcheck=all -finit-real=snan"
         echo > most_precision_options "MOST_PREC=-fdefault-real-8"
      # flags for gfortran version 4.5 - 4.8
      elif [ "$GFVER" -ge "405" ] ; then
         MOST_F90_OPTS="-O3 -funroll-loops -ffpe-trap=invalid,zero,overflow"
         DEBUG_F90_OPTS="-g -O0 -ffpe-trap=invalid,zero,overflow -fcheck=all -finit-real=snan"
         echo > most_precision_options "MOST_PREC=-fdefault-real-8"
      # flags for gfortran version 4.2, 4.3 and 4.4
      else
         MOST_F90_OPTS="-O3"
         DEBUG_F90_OPTS="-g -ffpe-trap=invalid,zero,overflow -fbounds-check"
      fi
      # tune for the build host: -march on x86, -mcpu on ARM and POWER
      case `uname -m` in
         x86_64|amd64|i?86)       ARCH_OPTS="-march=native" ;;
         arm64|aarch64|ppc64*)    ARCH_OPTS="-mcpu=native"  ;;
      esac
   else
      MOST_F90_OPTS="-O"
      DEBUG_F90_OPTS="-g"
   fi
   # host-specific options: user override, then check compiler support
   ARCH_OPTS="${MOST_ARCH_OPTS-$ARCH_OPTS}"
   if [ -n "$ARCH_OPTS" ] ; then
      if f90_accepts $MOST_F90 "$MOST_F90_OPTS $ARCH_OPTS" ; then
         MOST_F90_OPTS="$MOST_F90_OPTS $ARCH_OPTS"
         echo "Host-specific Fortran options   : $ARCH_OPTS"
      else
         echo "Host-specific Fortran options   : $ARCH_OPTS not supported - skipped"
         ARCH_OPTS=""
      fi
   fi
   echo  > most_compiler "MOST_F90=$F90_PATH"
   echo >> most_compiler "MOST_F90_OPTS=$MOST_F90_OPTS"
   echo >> most_compiler "MPIMOD=mpimod_stub"
   echo  > most_debug_options "MOST_F90_OPTS=$DEBUG_F90_OPTS"
else
   echo "****************************************************"
   echo "* Sorry - didn't find any FORTRAN-90 compiler      *"
   echo "* Please install one (e.g. gfortran or g95)        *"
   echo "* or update list of known compilers in this script *"
   echo "****************************************************"
   exit 1
fi


#check for Xlib
  if [ -e "/usr/X11/lib64/libX11.so" ] ; then
   XLIB_PATH="/usr/X11/lib64"
   XINC_PATH="/usr/X11/lib64/include"
elif [ -e "/usr/lib64/libX11.so" ] ; then
   XLIB_PATH="/usr/lib64"
   XINC_PATH="/usr/lib64/include"
elif [ -e "/usr/X11/lib" ] ; then
   XLIB_PATH="/usr/X11/lib"
   XINC_PATH="/usr/X11/include"
elif [ -e "/usr/lib/X11" ] ; then
   XLIB_PATH="/usr/lib/X11"
   XINC_PATH="/usr/lib/X11/include"
elif [ -e "/opt/X11" ] ; then
   XLIB_PATH="/opt/X11"
   XINC_PATH="/opt/X11/include"
fi
if [ -n ${XLIB_PATH} ] ; then
   echo "Found Xlib (X11)              at: $XLIB_PATH"
   GUILIB="-L$XLIB_PATH -lX11"
else
   echo "**********************************************"
   echo "* Didn't find Xlib (X11) at standard paths   *"
   echo "* Hopefully the compiler will find it itself *"
   echo "**********************************************"
   GUILIB=" -lX11"
fi

#check for C compiler
# put your favourite compiler in front if you have more than one

for MOST_CC in gcc cc gxlc suncc cc NO_CC
do
   `hash 2>/dev/null $MOST_CC`
   if [ $? = 0 ] ; then break ; fi
done

if [ $MOST_CC != "NO_CC" ] ; then
   CC_PATH=`which $MOST_CC`
   echo >> most_compiler "MOST_CC=$CC_PATH"
   echo >> most_compiler "MOST_CC_OPTS=-O3 -I" $XINC_PATH
   echo "Found C compiler              at: $CC_PATH"
   if [ $MOST_CC = "suncc" ] ; then
      echo >> most_debug_options "MOST_CC_OPTS=-g -C -ftrap=common"
   else
      echo >> most_debug_options "MOST_CC_OPTS=-g"
   fi
else
   echo "****************************************************"
   echo "* Sorry - didn't find any C compiler               *"
   echo "* Please install one (e.g. gcc or g++              *"
   echo "* or update list of known compilers in this script *"
   echo "****************************************************"
   exit 2
fi

# check for C++ compiler
# put your favourite compiler in front if you have more than one

for MOST_PP in c++ g++ NO_PP
do
   `hash 2>/dev/null $MOST_PP`
   if [ $? = 0 ] ; then break ; fi
done

if [ $MOST_PP != "NO_PP" ] ; then
   PP_PATH=`which $MOST_PP`
   echo >> most_compiler "MOST_PP=$PP_PATH"
   echo "Found C++ compiler            at: $PP_PATH"
else
   echo "****************************************************"
   echo "* Sorry - didn't find any C++ compiler             *"
   echo "* Please install one (e.g. c++ or g++              *"
   echo "* or update list of known compilers in this script *"
   echo "****************************************************"
   exit 2
fi

#check for MPI-FORTRAN-90 compiler
if [ "$MOST_F90" = "ifx" ] ; then
   MPI_F90_LIST="mpiifx mpiifort mpifc mpifort mpif90 openmpif90 mpf90 mpxlf90"
elif [ "$MOST_F90" = "ifort" ] ; then
   MPI_F90_LIST="mpiifort mpiifx mpifc mpifort mpif90 openmpif90 mpf90 mpxlf90"
else
   MPI_F90_LIST="mpifort openmpif90 mpif90 mpf90 mpxlf90 mpiifx mpiifort mpifc"
fi

BEST_MPI_F90="NO_F90"
for MPI_F90 in $MPI_F90_LIST
do
   if hash 2>/dev/null $MPI_F90 ; then
      if [ "$BEST_MPI_F90" = "NO_F90" ] ; then
         BEST_MPI_F90=$MPI_F90
      fi
      # When serial compiler is Intel, prefer a wrapper that accepts Intel options
      if [ "$MOST_F90" = "ifx" -o "$MOST_F90" = "ifort" ] ; then
         CAND_PATH=`which $MPI_F90`
         if f90_accepts $CAND_PATH "$MOST_F90_OPTS" || f90_accepts $CAND_PATH "-fc=ifx $MOST_F90_OPTS" ; then
            BEST_MPI_F90=$MPI_F90
            break
         fi
      else
         break
      fi
   fi
done
MPI_F90=$BEST_MPI_F90

if [ $MPI_F90 != "NO_F90" ] ; then
   MPI_F90_PATH=`which $MPI_F90`
   if [ $MPI_F90 = "openmpif90" ] ; then
      MPI_RUN="openmpiexec"
   else
      MPI_RUN="mpiexec"
   fi
   MPI_RUN_PATH=`which $MPI_RUN 2>/dev/null || echo $MPI_RUN`
   echo  > most_compiler_mpi "MPI_RUN=$MPI_RUN_PATH"
   echo >> most_compiler_mpi "MOST_F90=$MPI_F90_PATH"
   # the MPI wrapper may use another compiler than MOST_F90
   MPI_F90_OPTS="$MOST_F90_OPTS"
   if [ "$MOST_F90" = "ifx" ] ; then
      if f90_accepts $MPI_F90_PATH "-fc=ifx $MPI_F90_OPTS" ; then
         MPI_F90_OPTS="-fc=ifx $MPI_F90_OPTS"
      fi
   fi
   if ! f90_accepts $MPI_F90_PATH "$MPI_F90_OPTS" ; then
      ALT_OPTS=`echo "$MPI_F90_OPTS" | sed 's/-march=native/-march=core-avx2/'`
      if [ "$ALT_OPTS" != "$MPI_F90_OPTS" ] && f90_accepts $MPI_F90_PATH "$ALT_OPTS" ; then
         MPI_F90_OPTS="$ALT_OPTS"
      else
         echo "MPI FORTRAN-90 compiler rejects: $MPI_F90_OPTS - using -O3"
         MPI_F90_OPTS="-O3"
      fi
   fi
   echo >> most_compiler_mpi "MOST_F90_OPTS=$MPI_F90_OPTS"
   echo >> most_compiler_mpi "MPIMOD=mpimod"
   echo "Found MPI FORTRAN-90 compiler at: $MPI_F90_PATH"
else
   echo "********************************************"
   echo "* No Message Passing Interface (MPI) found *"
   echo "* Models run on single CPU                 *"
   echo "********************************************"
fi


#check for MPI-C compiler
if [ $MPI_F90 != "NO_F90" ] ; then
   if [ "$MOST_F90" = "ifx" ] ; then
      MPI_CC_LIST="mpiicx mpicc openmpicc mpiicc gxlc mpcc gcc"
   elif [ "$MOST_F90" = "ifort" ] ; then
      MPI_CC_LIST="mpiicc mpicc openmpicc mpiicx gxlc mpcc gcc"
   else
      MPI_CC_LIST="mpicc openmpicc mpiicx mpiicc gxlc mpcc gcc"
   fi
   for MPI_CC in $MPI_CC_LIST NO_CC
   do
      `hash 2>/dev/null $MPI_CC`
      if [ $? = 0 ] ; then break ; fi
   done
   if [ $MPI_CC != "NO_CC" ] ; then
      MPI_CC_PATH=`which $MPI_CC`
      echo >> most_compiler_mpi "MOST_CC=$MPI_CC_PATH"
      echo >> most_compiler_mpi "MOST_CC_OPTS=-O3"
      echo "Found MPI C compiler          at: $MPI_CC_PATH"
   else
      echo "********************************************"
      echo "* No MPI C compiler found                  *"
      echo "********************************************"
   fi
fi

#check for MPI-C++ compiler
if [ $MPI_F90 != "NO_F90" ] ; then
   if [ "$MOST_F90" = "ifx" ] ; then
      MPI_PP_LIST="mpiicpx mpicxx openmpicxx mpiicpc"
   elif [ "$MOST_F90" = "ifort" ] ; then
      MPI_PP_LIST="mpiicpc mpicxx openmpicxx mpiicpx"
   else
      MPI_PP_LIST="mpicxx openmpicxx mpiicpx mpiicpc"
   fi
   for MPI_PP in $MPI_PP_LIST NO_PP
   do
      `hash 2>/dev/null $MPI_PP`
      if [ $? = 0 ] ; then break ; fi
   done
   if [ $MPI_PP != "NO_PP" ] ; then
      MPI_PP_PATH=`which $MPI_PP`
      echo >> most_compiler_mpi "MOST_PP=$MPI_PP_PATH"
      echo >> most_compiler_mpi "MOST_PP_OPTS=-O3 -DMPI"
      echo >> most_debug_options "MOST_PP_OPTS=-g -DMPI"
      echo "Found MPI C++ compiler        at: $MPI_PP_PATH"
   else
      echo "********************************************"
      echo "* No MPI C++ compiler found                *"
      echo "********************************************"
   fi
fi

#check for 86_64 operating system
MACHINE=`uname -m`

#check for GNU assembler
for MOST_AS in as NO_AS
do
   `hash 2>/dev/null $MOST_AS`
   if [ $? = 0 ] ; then break ; fi
done

if [ $MOST_AS != "NO_AS" ] ; then
   AS_PATH=`which $MOST_AS`
   echo >> most_compiler     "MOST_AS=$AS_PATH"
   echo >> most_compiler_mpi "MOST_AS=$AS_PATH"
   echo "Found GNU assembler           at: $AS_PATH"
fi

# activate fast assembler Legendre module for OS X and Linux 64 bit
if [ $MACHINE = "x86_64" -a $MOST_AS = "as" ] ; then
   # use fast vectorized assembler routines for Legendre transformation
   echo >> most_compiler_mpi LEGMOD=legini
   echo >> most_compiler_mpi LEGFAST=legfast32.o
   echo >> most_compiler     LEGMOD=legini
   echo >> most_compiler     LEGFAST=legfast32.o
   UNAMES=`uname -s`
   # generate correct symbol names for accessing gfortran module variables
   if [ $UNAMES = "Darwin" ] ; then
      echo "Fast Legendre Transformation    : ACTIVE (Darwin)"
   else
      echo "Fast Legendre Transformation    : ACTIVE (Linux)"
   fi
else
   # use FORTRAN routines for Legendre transformation
   echo >> most_compiler_mpi LEGMOD=legsym
   echo >> most_compiler_mpi LEGFAST=
   echo >> most_compiler     LEGMOD=legsym
   echo >> most_compiler     LEGFAST=
fi

echo >> most_compiler     "GUILIB=$GUILIB"
echo >> most_compiler_mpi "GUILIB=$GUILIB"
echo >> most_compiler     "GUIMOD=guimod"
echo >> most_compiler_mpi "GUIMOD=guimod"
echo >> most_compiler     "PUMAX=pumax"
echo >> most_compiler_mpi "PUMAX=pumax"
echo  > makefile "most.x: most.c"
echo >> makefile "	$CC_PATH -o most.x most.c -I$XINC_PATH -lm $GUILIB"
echo >> makefile "clean:"
echo >> makefile "	rm -f *.o *.x F90* most_*"

#create directories

#mkdir -p puma/bld
#mkdir -p puma/bin
#mkdir -p puma/run
mkdir -p plasim/bld
mkdir -p plasim/bin
mkdir -p plasim/run
mkdir -p plasim/dat/T21_exo
mkdir -p plasim/dat/T42_exo
#mkdir -p cat/bld
#mkdir -p cat/bin
#mkdir -p cat/run
#mkdir -p sam/bld
#mkdir -p sam/bin
#mkdir -p sam/run

#check FORTRAN I/O

MOST_F90=$F90_PATH
MOST_CC=$CC_PATH
export MOST_F90
export MOST_CC
HOSTNAME=`hostname`
export HOSTNAME
MOSTARCH=`uname -a`
export MOSTARCH
make -e -f makecheck
./f90check.x
./cc_check.x
echo >> most_info.txt "FORTRAN Compiler: $F90_PATH"
echo >> most_info.txt "C       Compiler: $CC_PATH"
cat most_info.txt
make

echo
echo "configuration complete - run <most.x>"
echo
#
#end of configure.sh
