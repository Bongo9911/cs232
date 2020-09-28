# Multiply two numbers, found in locations 10 and 11, leaving the result in location 12.
# Assumes this code is loaded at location 20.
__main:
mov 0 12
mov *10 reg2
jez reg2 31
mov *11 reg1
jez reg1 31
mov reg2 reg0
sub 1 reg1
jez reg1 30
add reg0 reg2
jmp 26
mov reg2 12
end
