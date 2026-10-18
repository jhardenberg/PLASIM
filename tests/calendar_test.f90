program calendar_test
  implicit none
  character(len=32) :: mode, argument
  integer :: year_days, day, month, month_day

  call get_command_argument(1, mode)
  select case (trim(mode))
  case ('dates')
    call test_dates()
  case ('time')
    call test_time()
  case ('perpetual360')
    call check_simplified_year(30, 360)
    call check_simplified_year(55, 660)
  case ('perpetual365')
    call test_perpetual365()
  case ('interpolation')
    call test_interpolation()
  case ('invalid')
    call get_command_argument(2, argument)
    read(argument, *) year_days
    call get_command_argument(3, argument)
    read(argument, *) day
    call calini(year_days / 12, year_days, 0, 32, 86400.0, 1)
    call yday2mmdd(day, month, month_day)
    error stop 'Accepted invalid day of year'
  case default
    error stop 'Unknown calendar test case'
  end select

contains

  subroutine check(condition, message)
    logical, intent(in) :: condition
    character(len=*), intent(in) :: message
    if (.not. condition) then
      print *, message
      error stop 1
    endif
  end subroutine check

  subroutine test_dates()
    integer :: step, next_step, date(7), year

    call calini(30, 365, 0, 32, 86400.0, 1)
    call cal2step(step, 32, 0, 1, 1, 0, 0)
    call check(step == 0, 'Gregorian date origin')
    call cal2step(step, 32, 2000, 2, 29, 12, 0)
    call step2cal(step, 32, date)
    call check(all(date(1:5) == [2000, 2, 29, 12, 0]), 'Gregorian leap day')
    call cal2step(next_step, 32, 2000, 3, 1, 12, 0)
    call check(next_step - step == 32, '2000 leap day length')
    do year = 1900, 2100, 200
      call cal2step(step, 32, year, 2, 28, 0, 0)
      call cal2step(next_step, 32, year, 3, 1, 0, 0)
      call check(next_step - step == 32, 'Gregorian century rule')
      call step2cal(next_step, 32, date)
      call check(all(date(1:5) == [year, 3, 1, 0, 0]), 'Gregorian March boundary')
    enddo
    call cal2step(step, 32, 2000, 12, 31, 0, 0)
    call step2cal(step + 32, 32, date)
    call check(all(date(1:5) == [2001, 1, 1, 0, 0]), 'Gregorian year boundary')

    call calini(30, 360, 0, 32, 86400.0, 1)
    call cal2step(step, 32, 0, 1, 1, 0, 0)
    call check(step == 0, 'Simplified date origin')
    call cal2step(step, 32, 5, 2, 30, 0, 0)
    call step2cal30(step, 32, date)
    call check(all(date(1:5) == [5, 2, 30, 0, 0]), '360 day calendar')
    call step2cal30(step + 32, 32, date)
    call check(all(date(1:5) == [5, 3, 1, 0, 0]), '360 day month boundary')
    call cal2step(step, 32, 5, 12, 30, 0, 0)
    call step2cal30(step + 32, 32, date)
    call check(all(date(1:5) == [6, 1, 1, 0, 0]), '360 day year boundary')
  end subroutine test_dates

  subroutine test_time()
    integer :: midnight, step, date(7), offset, recovered

    call calini(30, 360, 0, 32, 86400.0, 1)
    call cal2step(midnight, 32, 5, 2, 30, 0, 0)
    call cal2step(step, 32, 5, 2, 30, 12, 0)
    call check(step - midnight == 16, 'Simplified noon must advance 16 steps')
    call cal2step(step, 32, 5, 2, 30, 0, 45)
    call check(step - midnight == 1, 'Simplified minute contribution')
    call cal2step(step, 32, 5, 2, 30, 1, 0)
    call check(step - midnight == 1, 'Non-aligned time truncates to preceding step')
    call step2cal30(step, 32, date)
    call check(all(date(4:5) == [0, 45]), 'Truncated time is 00:45')
    do offset = 0, 31
      call step2cal30(midnight + offset, 32, date)
      call cal2step(recovered, 32, date(1), date(2), date(3), date(4), date(5))
      call check(recovered == midnight + offset, 'Representable time round trip')
    enddo

    ! A two-Earth-day solar day has 90-minute timesteps at 32 steps/day.
    call calini(30, 360, 0, 32, 172800.0, 1)
    call cal2step(step, 32, 5, 2, 30, 12, 0)
    call check(step - midnight == 8, 'Configured solar day controls time conversion')
    call cal2step(step, 32, 5, 2, 30, 24, 0)
    call check(step - midnight == 16, '24 hours is half of a 48-hour solar day')
    do offset = 0, 31
      call step2cal30(midnight + offset, 32, date)
      call cal2step(recovered, 32, date(1), date(2), date(3), date(4), date(5))
      call check(recovered == midnight + offset, 'Non-Earth time round trip')
    enddo
  end subroutine test_time

  subroutine check_simplified_year(month_days, year_days)
    integer, intent(in) :: month_days, year_days
    integer :: day, month, month_day
    call calini(month_days, year_days, 0, 32, 86400.0, 1)
    do day = 1, year_days
      call yday2mmdd(day, month, month_day)
      call check(month == (day - 1) / month_days + 1, 'Perpetual month is one-based')
      call check(month_day == mod(day - 1, month_days) + 1, 'Simplified perpetual day')
    enddo
  end subroutine check_simplified_year

  subroutine check_fixed365()
    integer, parameter :: lengths(12) = [31,28,31,30,31,30,31,31,30,31,30,31]
    integer :: day, month, month_day, expected_month, expected_day
    day = 0
    do expected_month = 1, 12
      do expected_day = 1, lengths(expected_month)
        day = day + 1
        call yday2mmdd(day, month, month_day)
        call check(month == expected_month, 'Fixed-365 perpetual month')
        call check(month_day == expected_day, 'Fixed-365 perpetual day')
      enddo
    enddo
  end subroutine check_fixed365

  subroutine test_perpetual365()
    integer :: step, date(7)
    call calini(30, 365, 0, 32, 86400.0, 1)
    ! No previous dated conversion is required; later calls must not change it.
    call check_fixed365()
    call cal2step(step, 32, 2000, 2, 29, 0, 0)
    call check_fixed365()
    call step2cal(step, 32, date)
    call check_fixed365()
    call cal2step(step, 32, 1900, 3, 1, 0, 0)
    call check_fixed365()
  end subroutine test_perpetual365

  subroutine test_interpolation()
    integer, parameter :: year_lengths(3) = [360, 365, 660]
    integer, parameter :: month_lengths(3) = [30, 30, 55]
    integer :: config, day, month, month_day, step, a, b, ref_a, ref_b
    real :: weight, ref_weight, interpolated, expected
    real :: climate(0:13), tolerance

    ! Padding months 0 and 13 represent December and January respectively.
    climate(1:12) = [(real(month), month = 1, 12)]
    climate(0) = climate(12)
    climate(13) = climate(1)
    tolerance = 8.0 * epsilon(weight)
    do config = 1, size(year_lengths)
      call calini(month_lengths(config), year_lengths(config), 0, 32, 86400.0, 1)
      do day = 1, year_lengths(config)
        call yday2mmdd(day, month, month_day)
        ! A non-leap dated year must interpolate the same monthly climatology.
        call cal2step(step, 32, 2001, month, month_day, 0, 0)
        call momint(0, step, ref_a, ref_b, ref_weight)
        call momint(day, step, a, b, weight)
        call check(a >= 1 .and. a <= 12, 'Current climatology month in 1:12')
        call check(b >= 0 .and. b <= 13, 'Neighbor climatology month in 0:13')
        call check(weight >= 0.0 .and. weight <= 1.0, 'Bounded interpolation weight')
        call check(a == ref_a .and. b == ref_b, 'Perpetual and dated month indices')
        call check(abs(weight - ref_weight) <= tolerance, 'Perpetual and dated weights')
        interpolated = (1.0 - weight) * climate(a) + weight * climate(b)
        expected = (1.0 - ref_weight) * climate(ref_a) + ref_weight * climate(ref_b)
        call check(abs(interpolated - expected) <= 12.0 * tolerance, 'Monthly interpolation')
        if (day == 1) call check(a == 1 .and. b == 0, 'January uses December padding')
        if (day == year_lengths(config)) &
            call check(a == 12 .and. b == 13, 'December uses January padding')
      enddo
      ! Also check Gregorian perpetual interpolation after leap-year state.
      if (year_lengths(config) == 365) then
        call cal2step(step, 32, 2000, 2, 29, 0, 0)
        call momint(60, step, a, b, weight)
        call check(a == 3 .and. b == 2, 'Day 60 is March 1, even after leap day')
        call check(abs(weight - 15.0 / 29.5) <= tolerance, 'March 1 uses non-leap February')
      endif
    enddo
  end subroutine test_interpolation
end program calendar_test
