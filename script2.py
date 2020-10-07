
import sys

inputfile = sys.argv[1]
outputfile = sys.argv[2]
with open(inputfile, 'r') as infile, open(outputfile, 'w') as outfile:
    str1 = "CONSTRAINT"
    str2 = "\n"
    str3 = "CHECK"
    str4 = "000000"
    str5 = ".000000"
    str6 = "(PARTITION"
    str7 = "),"
    str8 = "NOT NULL,"
    str9 = "PLMODIFIEDDATETIME"
    str10 = "CREATE TABLE"
    str11 = "CREATE OR REPLACE TABLE"
    str12 = "NUMBER(*"
    str13 = "NUMBER(18"
    str14 = "REFERENCES"
    str15 = "TABLESPACE"
    str16 = "CREATE"
    str17 = ");"
    str18 = "SEGMENT CREATION IMMEDIATE"
    str19= "SEGMENT CREATION DEFERRED"
    a = []
    x = 0
    for lin in infile:
        a.append(lin)
        if str1 in a[x] and str2 in a[x - 1]:
            if str7 in a[x - 2]:
                a[x - 2] = a[x - 2].replace(str7, ")")
            elif str8 in a[x - 2]:
                a[x - 2] = a[x - 2].replace(str8, "NOT NULL")
            else:
                a[x - 2] = a[x - 2].replace(",", " ")
        elif str3 in a[x] and str2 in a[x - 1]:
            if str7 in a[x - 2]:
                a[x - 2] = a[x - 2].replace(str7, ")")
            elif str8 in a[x - 2]:
                a[x - 2] = a[x - 2].replace(str8, "NOT NULL")
            else:
                a[x - 2] = a[x - 2].replace(",", " ")
        elif str5 in a[x]:
            a[x] = a[x].replace(".000000", "--.000000")
        elif str4 in a[x]:
            a[x] = a[x].replace("000000", "--000000")
        elif str6 in a[x]:
            a[x] = a[x].replace("(", "--(")

        x = x + 1
    y = 0
    for l in a:
        if str9 in a[y]:
            a[y - 1] = a[y - 1].replace(")", "),")
        y = y + 1
    z = 0
    for l in a:
        if str10 in a[z]:
            a[z] = a[z].replace(str10, str11)
        z = z + 1
    w = 0
    for l in a:
        if str12 in a[w]:
            a[w] = a[w].replace(str12, str13)
        w = w + 1
    p = 0
    for l in a:
        if str14 in a[p]:
            a[p + 1] = " "
        p = p + 1

    q = 0
    for l in a:
        if str15 in a[q] and str16 in a[q + 2]:
            a[q + 1] = "select 'Compilation Done...';" + str2
        q = q + 1
    t = 0
    for l in a:
        if str18 in a[t] or str19 in a[t]:
            a[t - 1] = " "
        t = t + 1
    k = 0
    for l in a:
        if str11 in a[k]:
            a[k - 1] = str17 +str2
        k = k + 1


    if str17 in a[0]:
        a[0] = " "
    elif str17 in a[1] :
        a[1] = " "
    elif str17 in a[2] :
        a[2] = " "
    elif str17 in a[3] :
        a[3] = " "
    elif str17 in a[4] :
        a[4] = " "

    a[len(a)-1]= str17

    for li in a:
        outfile.write(li)
    print("Done Translating......")
