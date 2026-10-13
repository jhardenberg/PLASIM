program calendar_test
  implicit none
  integer :: step, next_step, date(7)

  ! Gregorian leap day exists in 2000.
  call calini(30, 365, 0, 32, 86400.0, 1)
  call cal2step(step, 32, 2000, 2, 29, 12, 0)
  call step2cal(step, 32, date)
  if (any(date(1:5) /= [2000, 2, 29, 12, 0])) &
      error stop 'Gregorian leap day'
  call cal2step(next_step, 32, 2000, 3, 1, 12, 0)
  if (next_step - step /= 32) error stop '2000 leap day length'

  ! 1900 is not a Gregorian leap year.
  call cal2step(step, 32, 1900, 2, 28, 0, 0)
  call cal2step(next_step, 32, 1900, 3, 1, 0, 0)
  if (next_step - step /= 32) error stop '1900 century rule'

  ! The model also supports a 360 day calendar.
  call calini(30, 360, 0, 32, 86400.0, 1)
  call cal2step(step, 32, 5, 2, 30, 0, 0)
  call step2cal30(step, 32, date)
  if (any(date(1:5) /= [5, 2, 30, 0, 0])) &
      error stop '360 day calendar'
end program calendar_test
