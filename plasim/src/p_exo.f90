!***********************************!
! Earth module for Planet Simulator !
!***********************************!

subroutine planet_ini
use radmod           ! Includes pumamod

logical :: lex

! Preset parameters may be changed using the namelist

namelist /planet_nl/ nfixorb, eccen, mvelp, obliq  &
                , rotspd, sidereal_day, solar_day  &
                , akap, alr, gascon, ra1, ra2, ra4 &
                , pnu, ga, plarad, psurf &
                , gsol0 &
                , yplanet,p_wsmax,tl_substellar,ltidally_locked
!                , sidereal_year, tropical_year     &


yplanet = "Exo"      ! Planet name
!nplanet = 1

! *********
! Astronomy
! *********

eccen         =     0.016715  ! Eccentricity (AMIP-II value) (GM)
mvelp         =   102.7       ! Longitude of perihelion
nfixorb       =     1          ! Don't use Berger orbits
obliq         =    23.441     ! Obliquity [deg] (AMIP-II) (GM)
rotspd        =     1.0       ! Rotation speed (factor)  (JJ useful?)
sidereal_day  =    86164.0916 !      23h 56m 04sa  (GM)
solar_day     =    86400.0    !      24h 00m 00s   (should be derived JJ)
!sidereal_year = 31558149.0    ! 365d 06h 09m 09s   (GM)
!tropical_year = 31556956.0    ! 365d 05h 49m 16s
ltidally_locked = .false.
tl_substellar = 180.0

! **********
! Atmosphere
! **********

akap    =   0.286     ! Kappa (Poisson constant R/Cp) 
alr     =   0.0065    ! Lapse rate
gascon  = 287.0       ! Gas constant
psurf   = 101100.0       ! Mean surface pressure [Pa]       (GM)
ra1     = 610.78      ! Parameter for Magnus-Teten-Formula
ra2     =  17.2693882 ! for saturation vapor pressure
ra4     =  35.86      ! over liquid water
tgr     = 288.0       ! mean ground temperature

! ********
! Calendar
! ********

n_days_per_month =  30 !
n_days_per_year  = 360 ! if set to 365 uses real Earth calendar

! ********
! Numerics
! ********

ndivdamp = 0         ! Initial start divergence damping
pnu      = 0.1       ! Time filter constant
oroscale = 1.0       ! Scale orography

! *******
! Physics
! *******

ga            =       9.80665 ! Gravity (mean on NN) (GM)
plarad        = 6371220.0     ! Radius   (GM)

! *********
! Radiation
! *********

gsol0         = 1365.0     ! Solar constant  (GM)
no3     = 1      ! switch for ozone (0=no,1=yes,2=datafile)

! *********
! Land
! *********

p_wsmax = 0.5   ! Maximum field capacity (m)

! ********
! Namelist
! ********

if (mypid == NROOT) then
   inquire(file=planet_namelist,exist=lex)
   if (lex) then
      open (nut,file=planet_namelist)
      read (nut,planet_nl)
      close(nut)
   endif
   write(nud,'(/,"****************************************")')
   write(nud,'("* planet_nl from    <",a16,"> *")') planet_namelist
   write(nud,'("****************************************")')
   write(nud,planet_nl)

endif ! (mypid == NROOT)

return
end


subroutine print_planet
use radmod

!p_sidorbit    =  sidereal_year / sidereal_day ! Sidereal orbit period

write(nud,4000)
write(nud,1000)
write(nud,1100) 'Simulating:',yplanet
write(nud,1000)
write(nud,2000) 'Parameter','Units','Value'
write(nud,1000)
write(nud,3000) 'Mean radius'      ,'[km]'        ,plarad/1000.0
write(nud,3000) 'Surface gravity'  ,'[m/s2]'      ,ga
write(nud,3000) 'Solar irradiance' ,'[W/m2]'      ,gsol0
!write(nud,3000) 'Sidereal orbit period' ,'[days]' ,p_sidorbit
write(nud,3000) 'Sidereal rotation period','[h]'  ,sidereal_day/3600.0
write(nud,3000) 'Mean surface pressure' ,'[Pa]'   ,psurf
write(nud,1000)
write(nud,4000)

if (nfixorb /= 0) then
   write(nud,3010) 'Using fixed orbit'       ,' '
   write(nud,3000) 'Longitude of perihelion' ,'[deg]' ,mvelp
   write(nud,3000) 'Equatorial inclination'  ,'[deg]' ,obliq
   write(nud,3000) 'Orbit eccentricity'      ,' '     ,eccen
else
   write(nud,3010) 'Using Berger orbit' ,'nfixorb=0'
endif

write(nud,3000) 'Rotation factor'       ,' '      ,rotspd
write(nud,3000) 'Gas constant'          ,' '      ,gascon
write(nud,1000)
write(nud,4000)

return

 1000 format(50('*'))
 1100 format('* ',a24,1x,a21,' *')
 2000 format('* ',a24,1x,a11,a10,' *')
 3000 format('* ',a24,1x,a11,f10.4,' *')
 3010 format('* ',a24,1x,a11,10x  ,' *')
 4000 format(/)
      end  


!          ===========
!          PLANET_STEP
!          ===========

subroutine planet_step
return
end

!          ===========
!          PLANET_STOP
!          ===========

subroutine planet_stop
return
end

