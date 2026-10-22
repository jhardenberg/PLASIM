!     ==================
!     subroutine CLSGINI
!     ==================
!
      subroutine clsgini(kdatim,ktspd,kaomod,kcpl,kgui,pslm,kxa,kya)
!
      real :: pslm(kxa,kya)
      integer :: kdatim(7)
      integer :: ktspd
      integer :: kaomod
      integer :: kcpl
      integer :: kgui
      integer :: kxa,kya
!
      return
      end subroutine clsgini
!
!     ===================
!     subroutine CLSGSTEP
!     ===================
!
      subroutine clsgstep(kdatim,kstep,psst,ptaux,ptauy,ppme,proff,pice &
     &                   ,pheat,pfldo)
!
      real :: psst(*)      ! atm sst (input)
      real :: ptaux(*)     ! atm u-stress (input)
      real :: ptauy(*)     ! atm v-stress (input)
      real :: ppme(*)      ! atm P-E fresh water flux (input)
      real :: proff(*)     ! atm river runoff flux (input)
      real :: pice(*)      ! atm ice thickness (incl. snow) (input)
      real :: pheat(*)     ! atm heat flux (input; not used yet)
      real :: pfldo(*)     ! atm deep ocean heat flux (output)
      integer :: kdatim(7) ! date and time
      integer :: kstep     ! current atm time step
!
      return
      end subroutine clsgstep
!
!     ===================
!     subroutine CLSGSTOP
!     ===================
!
      subroutine clsgstop
!
      return
      end subroutine clsgstop
