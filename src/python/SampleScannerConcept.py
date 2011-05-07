
col = [0,0,1,3,5,4,3,0,0,0,0,0,0,2,4,5,3,1,0,0]

# Durchschnitt

sum = 0
count = 0
for value in col:
    sum += value
    count+=1

limit = sum/count

# Durchschnitt ist limit

sum = .0
count = 0
open = None

for pos in range(len(col)):
    if (col[pos] > limit):
        if not open:
            open = pos

        sum += (pos * col[pos])
        count += col[pos]
    else:
        if open:
            open = None
            #Position der höchsten Intensität
            print sum/count
            sum = .0
            count = 0

