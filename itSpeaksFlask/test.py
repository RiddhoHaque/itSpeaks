def parity(num):
	cnt=0
	while num>0:
		if((num & 1)!=0):
			cnt=cnt+1
		num=num>>1
	return cnt

print(parity(511))

for i in range(10):
	print(i)
