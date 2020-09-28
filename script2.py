inputfilename=input ("Enter the inputfile name")
with open(inputfilename, 'r') as infile, open(r'output.txt', 'w') as outfile:
 str1 = "CONSTRAINT"
 str2 = "\n"
 str3= "CHECK"
 str4= "000000"
 str5= ".000000"
 str6= "(PARTITION"
 str7= "),"
 str8= "NOT NULL,"
 str9= "PLMODIFIEDDATETIME"
 a=[]
 x=0
 for lin in infile:
     a.append(lin)
     if str1 in a[x] and str2 in a[x - 1]:
         if str7 in a[x-2]:
             a[x - 2] = a[x - 2].replace(str7,")")
         elif str8 in a[x-2]:
             a[x - 2] = a[x - 2].replace(str8,"NOT NULL")
         else:
            a[x-2]=a[x-2].replace(","," ")
     elif str3 in a[x] and str2 in a[x - 1]:
         a[x - 2] = a[x - 2].replace(",", " ")
     elif str5 in a[x]:
         a[x]=a[x].replace(".000000","--.000000")
     elif str4 in a[x]:
         a[x]=a[x].replace("000000","--000000")
     elif str6 in a[x]:
         a[x]=a[x].replace("(","--(")

     x = x + 1
 y=0
 for l in a:
     if str9 in a[y]:
         a[y-1]= a[y-1].replace(")","),")
     y=y+1
 for li in a:
     outfile.write(li)



