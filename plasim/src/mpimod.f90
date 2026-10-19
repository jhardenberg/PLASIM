      module mpimod
      use pumamod
!      include 'mpif.h'
      use mpi

      integer :: mpi_itype = MPI_INTEGER4
      integer :: mpi_rtype = MPI_REAL4
      integer :: mpi_ltype = MPI_LOGICAL

      character(len=80) ynode(NPRO)           ! node names

      end module mpimod
!
!     interface routines to MPI:
!


!     ================
!     SUBROUTINE MPBCI
!     ================

      subroutine mpbci(k) ! broadcast 1 integer
      use mpimod
      integer :: k(*)

      call mpi_bcast(k,1,mpi_itype,NROOT,myworld,mpinfo)

      return
      end subroutine mpbci

!     =================
!     SUBROUTINE MPBCIN
!     =================

      subroutine mpbcin(k,n) ! broadcast n integer
      use mpimod

      integer :: k(n)

      call mpi_bcast(k,n,mpi_itype,NROOT,myworld,mpinfo)

      return
      end subroutine mpbcin

!     ================
!     SUBROUTINE MPBCR
!     ================

      subroutine mpbcr(p) ! broadcast 1 real
      use mpimod
      REAL :: p(*)

      call mpi_bcast(p,1,mpi_rtype,NROOT,myworld,mpinfo)

      return
      end subroutine mpbcr

!     =================
!     SUBROUTINE MPBCRN
!     =================

      subroutine mpbcrn(p,n) ! broadcast n real
      use mpimod
      real :: p(n)

      call mpi_bcast(p,n,mpi_rtype,NROOT,myworld,mpinfo)

      return
      end subroutine mpbcrn

!     ================
!     SUBROUTINE MPBCL
!     ================

      subroutine mpbcl(l) ! broadcast 1 logical
      use mpimod
      logical :: l(*)

      call mpi_bcast(l,1,mpi_ltype,NROOT,myworld,mpinfo)

      return
      end subroutine mpbcl

!     =================
!     SUBROUTINE MPSCIN
!     =================

      subroutine mpscin(k,n) ! scatter n integer
      use mpimod

      integer :: k(n),l(n)

      call mpi_scatter(k,n,mpi_itype,l,n,mpi_itype,NROOT,myworld,mpinfo)
      k(:)=l(:)

      return
      end subroutine mpscin

!     =================
!     SUBROUTINE MPSCRN
!     =================

      subroutine mpscrn(p,n) ! scatter n real
      use mpimod

      real :: p(*),l(n)
     
      call mpi_scatter(p,n,mpi_rtype,l,n,mpi_rtype,NROOT,myworld,mpinfo)
      p(1:n)=l(:)

      return
      end subroutine mpscrn

!     =================
!     SUBROUTINE MPSCDN
!     =================

      subroutine mpscdn(p,n) ! scatter n double precision
      use mpimod

      real (kind=8) :: p(*),l(n)

      call mpi_scatter(p,n,MPI_REAL8,l,n,MPI_REAL8,NROOT,myworld,mpinfo)
      p(1:n)=l(:)

      return
      end subroutine mpscdn

!     =================
!     SUBROUTINE MPSCGP
!     =================

      subroutine mpscgp(pf,pp,klev) ! scatter gridpoint fields
      use mpimod

      real :: pf(NUGP,klev)
      real :: pp(NHOR,klev)
      real :: zbuf(NHOR,klev,NPRO)
      integer :: jpro

      if (klev <= 1) then
         call mpi_scatter(pf(:,1),NHOR,mpi_rtype,                       &
     &                    pp(:,1),NHOR,mpi_rtype,                       &
     &                    NROOT,myworld,mpinfo)
      else
         if (mypid == NROOT) then
            do jpro = 1 , NPRO
               zbuf(:,:,jpro) = pf((jpro-1)*NHOR+1:jpro*NHOR,1:klev)
            enddo
         endif
         call mpi_scatter(zbuf,NHOR*klev,mpi_rtype,                     &
     &                    pp,NHOR*klev,mpi_rtype,                       &
     &                    NROOT,myworld,mpinfo)
      endif

      return
      end subroutine mpscgp

!     =================
!     SUBROUTINE MPGAGP
!     =================

      subroutine mpgagp(pf,pp,klev) ! gather gridpoint fields
      use mpimod

      real :: pf(NLON*NLAT,klev)
      real :: pp(NHOR,klev)
      real :: zbuf(NHOR,klev,NPRO)
      integer :: jpro

      if (klev <= 1) then
         call mpi_gather(pp(:,1),NHOR,mpi_rtype,                        &
     &                   pf(:,1),NHOR,mpi_rtype,                        &
     &                   NROOT,myworld,mpinfo)
      else
         call mpi_gather(pp,NHOR*klev,mpi_rtype,                        &
     &                   zbuf,NHOR*klev,mpi_rtype,                      &
     &                   NROOT,myworld,mpinfo)
         if (mypid == NROOT) then
            do jpro = 1 , NPRO
               pf((jpro-1)*NHOR+1:jpro*NHOR,1:klev) = zbuf(:,:,jpro)
            enddo
         endif
      endif

      return
      end subroutine mpgagp

!     ===================
!     SUBROUTINE MPGALLGP
!     ===================

      subroutine mpgallgp(pf,pp,klev) ! gather gritpoint to all
      use mpimod

      real :: pf(NLON*NLAT,klev)
      real :: pp(NHOR,klev)
      real :: zbuf(NHOR,klev,NPRO)
      integer :: jpro

      if (klev <= 1) then
         call mpi_allgather(pp(:,1),NHOR,mpi_rtype,                     &
     &                      pf(:,1),NHOR,mpi_rtype,                     &
     &                      myworld,mpinfo)
      else
         call mpi_allgather(pp,NHOR*klev,mpi_rtype,                     &
     &                      zbuf,NHOR*klev,mpi_rtype,                   &
     &                      myworld,mpinfo)
         do jpro = 1 , NPRO
            pf((jpro-1)*NHOR+1:jpro*NHOR,1:klev) = zbuf(:,:,jpro)
         enddo
      endif

      return
      end subroutine mpgallgp

!     =========================
!     SUBROUTINE MPSHIFTGP_NORTH
!     =========================
!     Shift a 2D gridpoint field 1 latitude row north (pout(:,j) = pin(:,j+1))
!     by exchanging only the boundary latitude row with neighboring MPI ranks
!     instead of gathering and scattering the full global grid in mkradv.

      subroutine mpshiftgp_north(pin,pout) ! shift global grid 1 row north
      use mpimod

      real :: pin(NLON,NLPP)
      real :: pout(NLON,NLPP)
      real :: zsend(NLON),zrecv(NLON)
      integer :: isrc,idst,istat(MPI_STATUS_SIZE)

      zsend(:) = pin(:,1)
      zrecv(:) = 0.0
      idst = mypid - 1
      if (idst < 0) idst = MPI_PROC_NULL
      isrc = mypid + 1
      if (isrc >= NPRO) isrc = MPI_PROC_NULL
      if (NPRO > 1) then
         call mpi_sendrecv(zsend,NLON,mpi_rtype,idst,101,               &
     &                     zrecv,NLON,mpi_rtype,isrc,101,               &
     &                     myworld,istat,mpinfo)
      endif
      if (NLPP > 1) pout(:,1:NLPP-1) = pin(:,2:NLPP)
      pout(:,NLPP) = zrecv(:)

      return
      end subroutine mpshiftgp_north

!     =========================
!     SUBROUTINE MPSHIFTGP_SOUTH
!     =========================
!     Shift a 2D gridpoint field 1 latitude row south (pout(:,j) = pin(:,j-1))
!     by exchanging only the boundary latitude row with neighboring MPI ranks.

      subroutine mpshiftgp_south(pin,pout) ! shift global grid 1 row south
      use mpimod

      real :: pin(NLON,NLPP)
      real :: pout(NLON,NLPP)
      real :: zsend(NLON),zrecv(NLON)
      integer :: isrc,idst,istat(MPI_STATUS_SIZE)

      zsend(:) = pin(:,NLPP)
      zrecv(:) = 0.0
      idst = mypid + 1
      if (idst >= NPRO) idst = MPI_PROC_NULL
      isrc = mypid - 1
      if (isrc < 0) isrc = MPI_PROC_NULL
      if (NPRO > 1) then
         call mpi_sendrecv(zsend,NLON,mpi_rtype,idst,102,               &
     &                     zrecv,NLON,mpi_rtype,isrc,102,               &
     &                     myworld,istat,mpinfo)
      endif
      if (NLPP > 1) pout(:,NLPP:2:-1) = pin(:,NLPP-1:1:-1)
      pout(:,1) = zrecv(:)

      return
      end subroutine mpshiftgp_south

!     =================
!     SUBROUTINE MPSCSP
!     =================

      subroutine mpscsp(pf,pp,klev) ! scatter spectral fields
      use mpimod

      real :: pf(NESP,klev)
      real :: pp(NSPP,klev)
      real :: zbuf(NSPP,klev,NPRO)
      integer :: jpro

      if (klev <= 1) then
         call mpi_scatter(pf(:,1),NSPP,mpi_rtype                        &
     &                   ,pp(:,1),NSPP,mpi_rtype                        &
     &                   ,NROOT,myworld,mpinfo)
      else
         if (mypid == NROOT) then
            do jpro = 1 , NPRO
               zbuf(:,:,jpro) = pf((jpro-1)*NSPP+1:jpro*NSPP,1:klev)
            enddo
         endif
         call mpi_scatter(zbuf,NSPP*klev,mpi_rtype                      &
     &                   ,pp,NSPP*klev,mpi_rtype                        &
     &                   ,NROOT,myworld,mpinfo)
      endif

      return
      end subroutine mpscsp

!     =================
!     SUBROUTINE MPGASP
!     =================

      subroutine mpgasp(pf,pp,klev) ! gather spectral fields
      use mpimod

      real :: pf(NESP,klev)
      real :: pp(NSPP,klev)
      real :: zbuf(NSPP,klev,NPRO)
      integer :: jpro

      if (klev <= 1) then
         call mpi_gather(pp(:,1),NSPP,mpi_rtype                         &
     &                  ,pf(:,1),NSPP,mpi_rtype                         &
     &                  ,NROOT,myworld,mpinfo)
      else
         call mpi_gather(pp,NSPP*klev,mpi_rtype                         &
     &                  ,zbuf,NSPP*klev,mpi_rtype                       &
     &                  ,NROOT,myworld,mpinfo)
         if (mypid == NROOT) then
            do jpro = 1 , NPRO
               pf((jpro-1)*NSPP+1:jpro*NSPP,1:klev) = zbuf(:,:,jpro)
            enddo
         endif
      endif

      return
      end subroutine mpgasp

!     =================
!     SUBROUTINE MPGACS
!     =================

      subroutine mpgacs(pcs) ! gather cross sections
      use mpimod

      real :: pcs(NLAT,NLEV),l(NLPP,NLEV)
      real :: zbuf(NLPP,NLEV,NPRO)
      integer :: jpro

      l(:,:) = pcs(1:NLPP,1:NLEV)
      call mpi_gather(l,NLPP*NLEV,mpi_rtype                             &
     &               ,zbuf,NLPP*NLEV,mpi_rtype                          &
     &               ,NROOT,myworld,mpinfo)
      if (mypid == NROOT) then
         do jpro = 1 , NPRO
            pcs((jpro-1)*NLPP+1:jpro*NLPP,1:NLEV) = zbuf(:,:,jpro)
         enddo
      endif
      return
      end subroutine mpgacs

!     ===================
!     SUBROUTINE MPGALLSP
!     ===================

      subroutine mpgallsp(pf,pp,klev) ! gather spectral to all
      use mpimod

      real :: pf(NESP,klev)
      real :: pp(NSPP,klev)
      real :: zbuf(NSPP,klev,NPRO)
      integer :: jpro

      if (klev <= 1) then
         call mpi_allgather(pp(:,1),NSPP,mpi_rtype                      &
     &                     ,pf(:,1),NSPP,mpi_rtype                      &
     &                     ,myworld,mpinfo)
      else
         call mpi_allgather(pp,NSPP*klev,mpi_rtype                      &
     &                     ,zbuf,NSPP*klev,mpi_rtype                    &
     &                     ,myworld,mpinfo)
         do jpro = 1 , NPRO
            pf((jpro-1)*NSPP+1:jpro*NSPP,1:klev) = zbuf(:,:,jpro)
         enddo
      endif

      return
      end subroutine mpgallsp

!     ================
!     SUBROUTINE MPSUM
!     ================

      subroutine mpsum(psp,klev) ! sum spectral fields
      use mpimod

      real :: psp(NESP*klev)
      real :: tmp(NESP*klev)

      call mpi_reduce(psp,tmp,NESP*klev,mpi_rtype,MPI_SUM     &
     &               ,NROOT,myworld,mpinfo)
      if (mypid == NROOT) psp = tmp

      return
      end subroutine mpsum

!     ==================
!     SUBROUTINE MPSUMSC
!     ==================

      subroutine mpsumsc(psf,psp,klev) ! sum & scatter spectral
      use mpimod

      real :: psf(NESP,klev)
      real :: psp(NSPP,klev)
      real :: zbuf(NSPP,klev,NPRO)
      integer :: iscat(NPRO)
      integer :: jpro

      if (klev <= 1) then
         call mpi_reduce_scatter(psf(:,1),psp(:,1),nscatsp              &
     &                          ,mpi_rtype,MPI_SUM,myworld,mpinfo)
      else
         do jpro = 1 , NPRO
            zbuf(:,:,jpro) = psf((jpro-1)*NSPP+1:jpro*NSPP,1:klev)
         enddo
         iscat(:) = NSPP * klev
         call mpi_reduce_scatter(zbuf,psp,iscat                         &
     &                          ,mpi_rtype,MPI_SUM,myworld,mpinfo)
      endif

      return
      end subroutine mpsumsc

!     ====================
!     SUBROUTINE MPSUMR
!     ====================

      subroutine mpsumr(pr,kdim) ! sum kdim reals
      use mpimod

      real pr(kdim)
      real tmp(kdim)

      call mpi_reduce(pr,tmp,kdim,mpi_rtype,MPI_SUM,NROOT,myworld,mpinfo)
      if (mypid == NROOT) pr = tmp

      return
      end subroutine mpsumr

!     ====================
!     SUBROUTINE MPSUMBCR
!     ====================

      subroutine mpsumbcr(pr,kdim) ! sum & broadcast kdim reals
      use mpimod

      real pr(kdim)
      real tmp(kdim)

      call mpi_allreduce(pr,tmp,kdim,mpi_rtype,MPI_SUM,myworld,mpinfo)
      pr = tmp

      return
      end subroutine mpsumbcr


!     ==================
!     SUBROUTINE MPABORT
!     ==================

      subroutine mpabort(ym)
      use mpimod

      character (len=* ) :: ym
      character (len=64) :: ystar = ' '
      character (len=64) :: yline = ' '
      character (len=64) :: yabor = 'Program aborted'
      character (len=64) :: ymess = ' '
      character (len=64) :: yhead = ' '

      ilmess = len_trim(ym)
      ilabor = len_trim(yabor)
      ilen   = 60

      do j = 1 , ilen+4
         ystar(j:j) = '*'
         yline(j:j) = '-'
      enddo

      ioff = 2
      if (ilmess < ilen-1) ioff = ioff + (ilen - ilmess) / 2
      ymess(1+ioff:ilmess+ioff) = trim(ym)

      ioff = 2
      if (ilabor < ilen-1) ioff = ioff + (ilen - ilabor) / 2
      yhead(1+ioff:ilabor+ioff) = trim(yabor)

      yline(1:1) = '*'
      ymess(1:1) = '*'
      yhead(1:1) = '*'
      yline(2:2) = ' '
      ymess(2:2) = ' '
      yhead(2:2) = ' '
      j = ilen + 4
      yline(j:j) = '*'
      ymess(j:j) = '*'
      yhead(j:j) = '*'
      j = ilen + 3
      yline(j:j) = ' '
      ymess(j:j) = ' '
      yhead(j:j) = ' '

      if (mypid == NROOT) then
         open (44,file='Abort_Message')
         write(44,'(A)') trim(ystar)
         write(44,'(A)') trim(yhead)
         write(44,'(A)') trim(yline)
         write(44,'(A)') trim(ymess)
         write(44,'(A)') trim(ystar)
         close(44)
         write(nud,'(/,A)') trim(ystar)
         write(nud,'(A)') trim(yhead)
         write(nud,'(A)') trim(yline)
         write(nud,'(A)') trim(ymess)
         write(nud,'(A,/)') trim(ystar)
      call mpi_abort(myworld,mpinfo,mpinfo)
      endif

      stop
      end
      

!     ==================
!     SUBROUTINE MPSTART
!     ==================

      subroutine mpstart(kworld) ! initialization
      use mpimod
      integer :: itest = 0
      real    :: rtest = 0.0
      logical :: ltest = .true.
      character (80) :: myympname

      if (kind(itest) == 8) mpi_itype = MPI_INTEGER8
      if (kind(rtest) == 8) mpi_rtype = MPI_REAL8

      if (kworld < 0) then
         call mpi_init(mpinfo)
         myworld=MPI_COMM_WORLD
      else
         myworld = kworld
      endif

      call mpi_comm_size(myworld,nproc,mpinfo)
      call mpi_comm_rank(myworld,mypid,mpinfo)

      if (nproc .ne. NPRO .and. mypid == NROOT) then
         write(nud,*)'Compiled for ',NPRO,' nodes'
         write(nud,*)'Running on ',nproc,' nodes'
         call mpi_abort(myworld,mpinfo,mpinfo)
      endif

      allocate(ympname(npro)) ; ympname(:) = ' '

      call mpi_get_processor_name(myympname,ilen,mpinfo)

      call mpi_gather(myympname,80,MPI_CHARACTER,   &   
                      ympname,80,MPI_CHARACTER,   &   
                      NROOT,myworld,mpinfo)
      return
      end subroutine mpstart

!     =================
!     SUBROUTINE MPSTOP
!     =================

      subroutine mpstop
      use mpimod

      call mpi_barrier(myworld,mpinfo)
      call mpi_finalize(mpinfo)

      return
      end subroutine mpstop

!     ===================
!     SUBROUTINE MPREADGP
!     ===================

      subroutine mpreadgp(ktape,p,kdim,klev)
      use mpimod

      real p(kdim,klev)
      real z(NLON*NLAT,klev)

      z = 0.0

      if (mypid == NROOT) read (ktape) z(:,:)

      if (kdim == NHOR) then
       call mpscgp(z,p,klev)
      else
       if (mypid == NROOT) p = z
      endif

      return
      end subroutine mpreadgp

!     ====================
!     SUBROUTINE MPWRITEGP
!     ====================

      subroutine mpwritegp(ktape,p,kdim,klev)
      use mpimod

      real p(kdim,klev)
      real z(NLON*NLAT,klev)

      if (kdim == NHOR) then
       call mpgagp(z,p,klev)
       if (mypid == NROOT) write(ktape) z(1:NLON*NLAT,:)
      else
       if (mypid == NROOT) write(ktape) p(1:NLON*NLAT,:)
      endif

      return
      end subroutine mpwritegp


!     =====================
!     SUBROUTINE MPWRITEGPH
!     =====================

      subroutine mpwritegph(ktape,p,kdim,klev,ihead)
      use mpimod

      real p(kdim,klev)
      real z(NLON*NLAT,klev)
!
      real(kind=4) :: zp(kdim,klev)
      real(kind=4) :: zz(NLON*NLAT,klev)
!

      integer ihead(8)

      if (kdim == NHOR) then
       call mpgagp(z,p,klev)
       if (mypid == NROOT) then
          write(ktape) ihead
          zz(:,:)=z(:,:)
          write(ktape) zz(1:NLON*NLAT,:)
       endif
      else
       if (mypid == NROOT) then
          write(ktape) ihead
          zp(:,:)=p(:,:)
          write(ktape) zp(1:NLON*NLAT,:)
       endif
      endif

      return
      end subroutine mpwritegph

!     ===================
!     SUBROUTINE MPREADSP
!     ===================

      subroutine mpreadsp(ktape,p,kdim,klev)
      use mpimod

      real p(kdim,klev)
      real z(NESP,klev)

      z = 0.0
      if (mypid == NROOT) read(ktape) ((z(i,j),i=1,NRSP),j=1,klev)
      if (kdim == NSPP) then
         call mpscsp(z,p,klev)
      else
         if (mypid == NROOT) p = z
      endif

      return
      end subroutine mpreadsp

!     ====================
!     SUBROUTINE MPWRITESP
!     ====================

      subroutine mpwritesp(ktape,p,kdim,klev)
      use mpimod

      real p(kdim,klev)
      real z(NESP,klev)

      if (kdim == NSPP) then
         call mpgasp(z,p,klev)
         if (mypid == NROOT) write(ktape) ((z(i,j),i=1,NRSP),j=1,klev)
      else
         if (mypid == NROOT) write(ktape) ((z(i,j),i=1,NRSP),j=1,klev)
      endif

      return
      end subroutine mpwritesp


!     ===================
!     SUBROUTINE GET_MPI_INFO
!     ===================

      subroutine get_mpi_info(nprocess,npid)    ! get nproc and pid
      use mpimod

      myworld=MPI_COMM_WORLD

      call mpi_comm_size(myworld,nprocess,mpinfo)
      call mpi_comm_rank(myworld,npid,mpinfo)

      return
      end subroutine get_mpi_info


!     ==================
!     SUBROUTINE MPGETSP
!     ==================

      subroutine mpgetsp(yn,p,kdim,klev)
      use mpimod

      character (len=*) :: yn
      real :: p(kdim,klev)
      real :: z(NESP,klev)

      z(:,:) = 0.0
      if (mypid == NROOT) call get_restart_array(yn,z,NRSP,NESP,klev)
      call mpscsp(z,p,klev)

      return
      end subroutine mpgetsp


!     ==================
!     SUBROUTINE MPGETGP
!     ==================

      subroutine mpgetgp(yn,p,kdim,klev)
      use mpimod

      character (len=*) :: yn
      real :: p(kdim,klev)
      real :: z(NUGP,klev)

      if (mypid == NROOT) call get_restart_array(yn,z,NUGP,NUGP,klev)
      call mpscgp(z,p,klev)

      return
      end subroutine mpgetgp


!     ==================
!     SUBROUTINE MPPUTSP
!     ==================

      subroutine mpputsp(yn,p,kdim,klev)
      use mpimod

      character (len=*) :: yn
      real :: p(kdim,klev)
      real :: z(NESP,klev)

      call mpgasp(z,p,klev)
      if (mypid == NROOT) call put_restart_array(yn,z,NRSP,NESP,klev)

      return
      end subroutine mpputsp


!     ==================
!     SUBROUTINE MPPUTGP
!     ==================

      subroutine mpputgp(yn,p,kdim,klev)
      use mpimod

      character (len=*) :: yn
      real :: p(kdim,klev)
      real :: z(NUGP,klev)

      call mpgagp(z,p,klev)
      if (mypid == NROOT) call put_restart_array(yn,z,NUGP,NUGP,klev)

      return
      end subroutine mpputgp


!     ===================
!     SUBROUTINE MPSURFGP
!     ===================

      subroutine mpsurfgp(yn,p,kdim,klev)
      use mpimod

      character (len=*) :: yn
      real :: p(kdim,klev)
      real :: z(NUGP,klev)
      integer :: iread(1)

      if (mypid == NROOT) call get_surf_array(yn,z,NUGP,klev,iread)
      call mpbci(iread)
      if (iread(1) == 1) call mpscgp(z,p,klev)

      return
      end subroutine mpsurfgp


!     ===================
!     SUBROUTINE MPMAXVAL
!     ===================

      subroutine mpmaxval(p,kdim,klev,pmax)
      use mpimod

      real :: p(kdim,klev)
      real :: pmax(1)
      real zmax(1)

      zmax(1) = maxval(p(:,:))
      call mpi_allreduce(zmax,pmax,1,mpi_rtype,MPI_MAX,myworld,mpinfo)

      return
      end subroutine mpmaxval


!     ===================
!     SUBROUTINE MPSUMVAL
!     ===================

      subroutine mpsumval(p,kdim,klev,psum)
      use mpimod

      real :: p(kdim,klev)
      real :: psum(1)
      real :: zsum(1)

      zsum = sum(p(:,:))
      call mpi_allreduce(zsum,psum,1,mpi_rtype,MPI_SUM,myworld,mpinfo)

      return
      end subroutine mpsumval

      subroutine mrsum(k) ! sum up 1 integer
      return
      end 

      subroutine mrbci(k) ! broadcast 1 integer
      return
      end 

      subroutine mrdiff(p,d,n)
      real :: p(n)
      real :: d(n)
      return
      end 

      subroutine mrdimensions ! used in mpimod_multi.f90
      return
      end 

