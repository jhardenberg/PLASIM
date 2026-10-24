!     ======================
!     MODULE NETCDFMOD (STUB)
!     ======================

      module netcdfmod
      use pumamod
      implicit none

      contains

      subroutine netcdf_init
         if (nnetcdf > 0) then
            if (mypid == NROOT) then
               write(*,*) 'Error: Direct NetCDF output requested (nnetcdf > 0)'
               write(*,*) '       but model was compiled with netcdfmod_stub.'
               write(*,*) '       Please recompile with NetCDF-Fortran support.'
            endif
            call mpabort('NetCDF output not available in stub build')
         endif
      end subroutine netcdf_init

      subroutine netcdf_step
      end subroutine netcdf_step

      subroutine netcdf_close
      end subroutine netcdf_close

      end module netcdfmod
