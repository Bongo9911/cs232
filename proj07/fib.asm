# Generate the fibonacci sequence.
# At location 50: number of iterations
# Output starts at 500.
# Assume code is loaded at location 100.
# Temp storage starts at 150.

__main: 100
# fib1 and fib2 values stored in locations 150, 151
# They start with values 1 and 1.
mov 1 150
mov 1 151

# Output first two fib #s. Assumes # of iterations > 2.
mov 1 500
mov 1 501
# Store output location in temp storage at 152.
mov 502 152
# Number of iterations left stored in 153, minus 2
# because we hard-code the first 2 numbers.
mov *50 reg0
sub 2 reg0
mov reg0 153


# LOOP: location 108
mov *153 reg0
# jump to the end
jez reg0 124

mov *150 reg0
mov *151 reg1
# copy 2nd number to reg2
mov reg1 reg2
# add first number
add reg0 reg2
# store 2nd number in first number temp memory
mov reg1 150
# store new number in 2nd number temp memory
mov reg2 151
# load output location into reg0
mov *152 reg0
# write new fib # to output
mov reg2 *reg0
# increment output location
add 1 reg0
mov reg0 152

# Decrement # of iterations left
mov *153 reg2
sub 1 reg2
mov reg2 153
jmp 108 
# END: location 124
end


