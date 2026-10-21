program defensive_test
  use cplmod, only: nud
  implicit none
  character(len=16) :: mode
  real :: field(2,2), output(2,2), mask(2,2), weights(2,2)
  real :: x(2,2), y(2,2), x1(2,2), x2(2,2), y1(2,2), y2(2,2)
  real :: total, mean, area, pi

  call get_command_argument(1, mode)
  open(nud, file='diagnostics.txt', status='replace')
  field = 2.0
  mask = 1.0
  weights = 1.0
  select case (trim(mode))
  case ('coupling')
    pi = 2.0 * asin(1.0)
    x1(1,:) = 0.0
    x1(2,:) = pi
    x2 = x1 + pi
    y1(:,1) = -pi * 0.5
    y1(:,2) = 0.0
    y2 = y1 + pi * 0.5
    x = (x1 + x2) * 0.5
    y = (y1 + y2) * 0.5
    call cinter(field,mask,output,mask,weights,weights,x1,x2,x1,x2, &
                y1,y2,y1,y2,2,2,2,2,2,1)
    if (any(abs(output - field) > 8.0 * epsilon(mean))) error stop 'CINTER result'
    call cinter2(field,mask,output,mask,weights,weights,x,x,y,y,2,2,2,2,2,1)
    if (any(abs(output - field) > 8.0 * epsilon(mean))) error stop 'CINTER2 result'
    output = field
    output(1,1) = -9.e9
    call cfill(output,mask,2,2,-9.e9,1)
    if (any(output /= field)) error stop 'CFILL result'
    output = 0.0
    call conserve(field,output,mask,mask,weights,weights,2,2,2,2,1,1)
    if (any(output /= 0.0)) error stop 'Zero-output conservation fallback'
    call cglm(field,mask,total,mean,area,weights,2,2)
    if (total /= 8.0 .or. mean /= 2.0 .or. area /= 4.0) error stop 'CGLM result'
    mask = 0.0
    mean = -999.0
    call cglm(field,mask,total,mean,area,weights,2,2)
    if (total /= 0.0 .or. mean /= 0.0 .or. area /= 0.0) error stop 'Empty-mask result'
  case ('restart')
    call check_equality('same', field, field, 2, 2)
    output = field
    output(2,1) = 3.0
    call check_equality('different', field, output, 2, 2)
  case default
    error stop 'Unknown defensive test case'
  end select
  close(nud)
end program defensive_test
