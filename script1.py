import sys
import regex
import re
import argparse

# VARCHAR2(n BYTE) => VARCHAR(n)
varchar2_regex = regex.compile('(.*)(VARCHAR2\((\d+)(\s+.+)?\))(.*)', regex.IGNORECASE)
clob_regex = regex.compile('(.*)\ (CLOB)(.*)', regex.IGNORECASE)
rowid_regex = regex.compile('(.*)\ (ROWID)(.*)', regex.IGNORECASE)
using_regex = regex.compile('(.*)\ (USING)\ (.*)', regex.IGNORECASE)
lob_regex = regex.compile('(.*)\ (LOB)\ (.*)', regex.IGNORECASE)
nocache_regex = regex.compile('(.*)\ (NOCACHE)\ (.*)', regex.IGNORECASE)
buffer_regex = regex.compile('(.*)\ (BUFFER_POOL)\ (.*)', regex.IGNORECASE)
partition_regex = regex.compile('(.*)\ ("(*"+PARTITION)\ (.*)', regex.IGNORECASE)
default_regex = regex.compile('(.*)\ (DEFAULT\s+(?:SYSTIMESTAMP|TO_TIMESTAMP))(.*)', regex.IGNORECASE)


# CHAR(n BYTE) => CHAR(n)
char_regex = regex.compile('(.*)(CHAR\((\d+)(\s+.+)\))(.*)', regex.IGNORECASE)

# DEFAULT SYSDATE => deleted (OK only because data loaded from table should already have date)
# Snowflake DEFAULT must be literal
default_sysdate_regex = regex.compile('(.*)\ (DEFAULT SYSDATE)\ (.*)', regex.IGNORECASE)

# SYSDATE => CURRENT_TIMESTAMP()
# sysdate_regex = regex.compile('(.*)\ (SYSDATE)\ (.*)', regex.IGNORECASE)
sysdate_regex = regex.compile('(.*[,\(\s])(SYSDATE)([,\)\s].*)', regex.IGNORECASE)

# SEGMENT CREATION type => ignore
segment_creation_regex = regex.compile('(.*)\ (SEGMENT\s+CREATION\s+(?:IMMEDIATE|DEFERRED))(.*)', regex.IGNORECASE)
# table_creation_regex = regex.compile('(.*)\ (CREATE\s+TABLE\s+())(.*)', regex.IGNORECASE)
nocompress_regex = regex.compile('(.*)\ (NOCOMPRESS\s+(?:LOGGING|DEFERRED))(.*)', regex.IGNORECASE)
pctfree_regex = regex.compile('(.*)\ (PCTFREE)(.*)', regex.IGNORECASE)
check_regex = regex.compile('(.*)\ (CHECK)(.*)', regex.IGNORECASE)
novalidate_regex = regex.compile('(.*)\ (NOVALIDATE)(.*)', regex.IGNORECASE)

# Percentage Increase type => ignore
pctinc_regex = regex.compile('(.*)\ (PCTINCREASE\s+)(.*)', regex.IGNORECASE)

# Header comments type => ignore
headercomments_regex = regex.compile('^[-]{3,}$', regex.IGNORECASE)

# DBMS Output type => ignore
dbmsoutput_regex = regex.compile('^DBMS_METADATA.GET_DDL\(OBJECT_TYPE,OBJECT_NAME,OWNER\)', regex.IGNORECASE)

# SC Tables Output type => ignore
sctables_regex = regex.compile('^\/\*<sc-table>', regex.IGNORECASE)

# SC Tables SingleQuote Output type => ignore
sctables_quote_regex = regex.compile("^'\/\*<sc-table>", regex.IGNORECASE)
# Buffer pool type => ignore
buff_regex = regex.compile('(.*)\ (BUFFER_POOL\s+)(.*)', regex.IGNORECASE)

# Tablespace type => ignore
tablespace_regex = regex.compile('(.*)\ (TABLESPACE)(.*)', regex.IGNORECASE)
constraint_regex = regex.compile('(.*)\ (CONSTRAINT)(.*)', regex.IGNORECASE)
# parallel type => ignore
parallel_regex = regex.compile('(.*)\ (PARALLEL)(.*)', regex.IGNORECASE)

# NOT NULL ENABLE => NOT NULL
not_null_enable_regex = regex.compile('(.*)(NOT\s+NULL\s+ENABLE)(.*)', regex.IGNORECASE)

# find prior period, e.g. trunc(col,'MM')-1 => dateadd('MM', -1, trunc(col, 'MM'))
prior_period_regex = regex.compile('(.*)(TRUNC\(\s*(.+?),\s*(\'.+?\')\s*\)\s*(-?\s*\d+))(.*)', regex.IGNORECASE)

# add months, e.g. add_months(trunc(col, 'MM'), -5) => dateadd(month, -5, col)
add_months_regex = regex.compile('(.*)(ADD_MONTHS\(\s*TRUNC\(\s*(.+?),\s*(\'.+?\')\s*\),\s*(-?\s*\d+))(.*)',
                                 regex.IGNORECASE)

### RegExes for SQL-Server dialect that Snowflake doesn't support

# NULL (explicit NULL constraint) -- ignore
null_constraint_regex = regex.compile('(.*)((?<!NOT)\s+NULL(?!::))(.*)', regex.IGNORECASE)
is_null_condition_regex = regex.compile('.*IS NULL.*', regex.IGNORECASE)

# NVARCHAR => VARCHAR
nvarchar_regex = regex.compile('(.*)\ (NVARCHAR)(.*)', regex.IGNORECASE)

# NVARCHAR => VARCHAR
nchar_regex = regex.compile('(.*)\ (NCHAR)(.*)', regex.IGNORECASE)

# ON PRIMARY => ignore
on_primary_regex = regex.compile('(.*)\ (ON PRIMARY)(.*)', regex.IGNORECASE)

# DATETIME => TIMESTAMP
datetime_regex = regex.compile('(.*)\ (DATETIME)(.*)', regex.IGNORECASE)

# BIT => BOOLEAN
bit_regex = regex.compile('(.*)\ (BIT)(.*)', regex.IGNORECASE)

### RegExes for Redshift dialect that Snowflake doesn't support

# DISTKEY(col) => ignore
# DISTKEY => ignore
distkey_regex = regex.compile('(.*)(\s*DISTKEY\s*(?:\(.*?\))?)(.*)', regex.IGNORECASE)

# SORTKEY(col) => ignore
sortkey_regex = regex.compile('(.*)(\s*SORTKEY\s*\(.*?\))(.*)', regex.IGNORECASE)

# SORTKEY => ignore through end of statement
sortkey_multiline_regex = regex.compile('(.*)(\s*SORTKEY\s*\(?\s*$)(.*)', regex.IGNORECASE)

# ENCODE type => ignore
encode_regex = regex.compile('(.*)(\sENCODE\s+.+?)((?:,|\s+|$).*)', regex.IGNORECASE)

# DISTSTYLE type => ignore
diststyle_regex = regex.compile('(.*)(\s*DISTSTYLE\s+.+?)((?:,|\s+|$).*)', regex.IGNORECASE)

# 'now'::character varying => current_timestamp
now_character_varying_regex = regex.compile('(.*)(\'now\'::(?:character varying|text))(.*)', regex.IGNORECASE)

# bpchar => char
bpchar_regex = regex.compile('(.*)(bpchar)(.*)', regex.IGNORECASE)

# character varying => varchar
character_varying_regex = regex.compile('(.*)(character varying)(.*)')

# interleaved => ignore
interleaved_regex = regex.compile('(.*)(interleaved)(.*)', regex.IGNORECASE)

# identity(start, 0, ([0-9],[0-9])::text) => identity(start, 1)
identity_regex = regex.compile('(.*)\s*DEFAULT\s*"identity"\(([0-9]*),.*?(?:.*?::text)\)(.*)', regex.IGNORECASE)

### RegExes for Netezza dialect that Snowflake doesn't support

## casting syntax
# INT4(expr) => expr::INTEGER
int4_regex = regex.compile('(.*)\ (INT4\s*\((.*?)\))(.*)', regex.IGNORECASE)

### RegExes for common/standard types that Snowflake doesn't support
bigint_regex = regex.compile('(.*)\ (BIGINT)(.*)', regex.IGNORECASE)
smallint_regex = regex.compile('(.*)\ (SMALLINT)(.*)', regex.IGNORECASE)
floatN_regex = regex.compile('(.*)\ (FLOAT\d+)(.*)', regex.IGNORECASE)

# CREATE [type] INDEX => ignore through end of statement
index_regex = regex.compile('(.*)(CREATE(?:\s+(?:UNIQUE|BITMAP))?\ INDEX)(.*)', regex.IGNORECASE)

# ALTER TABLE ... ADD PRIMARY KEY => ignore
pk_regex = regex.compile('(.*)(ALTER\s+TABLE\s+.*ADD\s+PRIMARY\s+KEY)(.*)', regex.IGNORECASE)

# SET ... TO => ignore
set_regex = regex.compile('(.*)(SET\s+.*TO)(.*)', regex.IGNORECASE)

statement_term_regex = regex.compile('(.*);(.*)', regex.IGNORECASE)


def make_snow(sqlin, sqlout, no_comments):
    ### processing mode
    comment_lines = None
    term_regex = None

    for line in sqlin:
        ### state variables
        pre = None
        clause = None
        post = None
        comment = None
        sql = line.rstrip()
        sql = sql.replace('[', '').replace(']', '')

        # print >> sys.stdout, 'input: ' + sql
        if pctinc_regex.match(sql):
            continue;

        if dbmsoutput_regex.match(sql):
            continue;

        if sctables_regex.match(sql):
            continue;
        if sctables_regex.match(sql):
            continue;

        if sctables_quote_regex.match(sql):
            continue;
        if headercomments_regex.match(sql):
            continue;
        # if re.match('^[ \-\-]+SEGMENT ',sql):
        #     sql = re.sub('^[ \-\-]+SEGMENT ', sql, ') /*')
        # if re.match('^[ \-\-]+PARALLEL ',sql):
        #     sql = re.sub('^[ \-\-]+PARALLEL ', sql, '*/')

        if comment_lines:
            result = term_regex.match(sql)
            if result:
                comment_lines = None
                term_regex = None
            sql = '-- {0}'.format(sql)

        # VARCHAR2(n BYTE) => VARCHAR(n)
        result = varchar2_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)  # varchar2 clause
            cnt = result.group(3)
            discard = result.group(4)
            post = result.group(5)
            sql = '{0}{1}({2}){3}\t\t-- {4}'.format(pre, clause[0:7], cnt, post, clause)

        # clob => VARCHAR(n)
        result = clob_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0} VARCHAR {1}\t\t-- {2}'.format(pre, post, " CLOB")

        # rowid => VARCHAR(n)
        result = rowid_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0} VARCHAR {1}\t\t-- {2}'.format(pre, post, " ROWID")

        # CHAR(n BYTE) => CHAR(n)
        result = char_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)  # char clause
            cnt = result.group(3)
            discard = result.group(4)
            post = result.group(5)
            sql = '{0}{1}({2}){3}\t\t-- {4}'.format(pre, clause[0:4], cnt, post, clause)

        # DEFAULT SYSDATE => deleted (OK only because data loaded from table should already have date)
        result = default_sysdate_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0} {1}\t\t-- {2}'.format(pre, post, clause)

        # NVARCHAR => VARCHAR
        result = nvarchar_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0} VARCHAR {1}\t\t-- {2}'.format(pre, post, clause)

        # NCHAR => CHAR
        result = nchar_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0} CHAR {1}\t\t-- {2}'.format(pre, post, clause)

        # DATETIME => TIMESTAMP
        result = datetime_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0} TIMESTAMP {1}\t\t-- {2}'.format(pre, post, clause)

        # BIGINT => INTEGER
        # result = bigint_regex.match(sql)
        # if result:
        #    pre = result.group(1)
        #    clause = result.group(2)
        #    post = result.group(3)
        #    sql = '{0} INTEGER {1}\t\t-- {2}'.format(pre, post, clause)

        # SMALLINT => INTEGER
        # result = smallint_regex.match(sql)
        # if result:
        #    pre = result.group(1)
        #    clause = result.group(2)
        #    post = result.group(3)
        #    sql = '{0} INTEGER {1}\t\t-- {2}'.format(pre, post, clause)

        # BIT => BOOLEAN
        result = bit_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0} BOOLEAN {1}\t\t-- {2}'.format(pre, post, clause)

        # FLOAT8 => FLOAT
        result = floatN_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0} FLOAT {1}\t\t-- {2}'.format(pre, post, clause)

        # NULL (without NOT) => implicit nullable
        result = null_constraint_regex.match(sql)
        if result and is_null_condition_regex.match(sql):
            # we are in query or DML, so not looking at a constraint
            result = None
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}{1}\t\t-- {2}'.format(pre, post, clause)

        # ON PRIMARY => ignore
        result = on_primary_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}{1}\t\t-- {2}'.format(pre, post, clause)

        # DISTKEY(col) => ignore
        result = distkey_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}{1}\t\t-- {2}'.format(pre, post, clause)

        # SORTKEY(col) => ignore
        result = sortkey_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}{1}\t\t-- {2}'.format(pre, post, clause)

        # SORTKEY => ignore through end of statement
        result = sortkey_multiline_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0};\n-- {2} {1}'.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex

        # ENCODE type => ignore
        result = encode_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}{1}\t\t-- {2}'.format(pre, post, clause)

        # DISTSTYLE type => ignore
        result = diststyle_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}{1}\t\t-- {2}'.format(pre, post, clause)

        # 'now'::(character varying|text) => current_timestamp
        result = now_character_varying_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}CURRENT_TIMESTAMP{1} --{2}'.format(pre, post, clause)

        # bpchar => char
        result = bpchar_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}char{1} --{2}'.format(pre, post, clause)

        result = character_varying_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}varchar{1}  --{2}'.format(pre, post, clause)

        # interleaved => ignore
        result = interleaved_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0} {1} --{2}'.format(pre, post, clause)

        result = identity_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0} IDENTITY({1},1) {2}'.format(pre, clause, post)

        result = partition_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}\n -- {2}  {1} '.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex

        result = lob_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}\n /* {2}  {1} '.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex

        result = nocache_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}\n /* {2}  {1} '.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex

        result = buffer_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}\n  {2}  {1}*/ '.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex

        # SEGMENT CREATION type => ignore

        result = segment_creation_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0};\n /* {2}  {1} '.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex

        # Parallel type => ignore
        result = parallel_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = "{0}\n-- {2} {1} */ \n select '--';".format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex

            # Constraint type  type => ignore

        result = constraint_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}\n /* {2}  {1} '.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex

        result = tablespace_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = "{0}\n -- {2}  {1} ".format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex

        # CHECK => COMMENT
        result = check_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}\n -- {2}  {1} '.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex


        result = default_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0},\n -- {2}  {1} '.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex




        """result = novalidate_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = "{0}\n  {2}  {1} */".format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex"""

        """result = table_creation_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0};\n {2} {1}'.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex"""

        # NOCOMPRESS CREATION type => ignore
        result = nocompress_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0};\n-- {2} {1} '.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex


            # using index type => ignore
        result = using_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}\n /*{2} {1} '.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex

            # pctfree CREATION type => ignore
        result = pctfree_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}\n/*{2} {1} '.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex

        # ALTER TABLE ... ADD PRIMARY KEY => ignore
        result = index_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}-- {2} {1}'.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex

        # INDEX CREATION => ignore through end of statement
        result = pk_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}-- {2} {1}'.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex

        # SET ... TO => ignore
        result = set_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}-- {2} {1}'.format(pre, post, clause)
            comment_lines = 0
            term_regex = statement_term_regex

        # NOT NULL ENABLE => NOT NULL
        result = not_null_enable_regex.match(sql)
        if result:
            pre = result.group(1)
            clause = result.group(2)
            post = result.group(3)
            sql = '{0}NOT NULL{1}\t\t-- {2}'.format(pre, post, clause)

        ## DML transformations that might appear multiple times per line
        dml_repeat = True
        while dml_repeat:
            dml_repeat = False

            # determine prior period
            # e.g. trunc(sysdate,'MM')-1
            result = prior_period_regex.match(sql)
            if result:
                pre = result.group(1)
                clause = result.group(2)
                col = result.group(3)
                units = result.group(4)
                offset = result.group(5)
                post = result.group(6)
                sql = '{0}dateadd({4}, {5}, trunc({3}, {4}))'.format(pre, post, clause, col, units, offset)
                comment = append_comment(comment, clause, no_comments)
                dml_repeat = True

            # add_months
            # e.g. add_months(trunc(sysdate, 'MM'), -5) => dateadd('MM', -5, trunc(current_timestamp, 'MM'))
            result = add_months_regex.match(sql)
            if result:
                raise Exception("Snowflake now has add_months() function -- verify can use as-is")

            # SYSDATE => CURRENT_TIMESTAMP()
            result = sysdate_regex.match(sql)
            if result:
                pre = result.group(1)
                clause = result.group(2)
                post = result.group(3)
                sql = '{0} CURRENT_TIMESTAMP() {1}'.format(pre, post, clause)
                comment = append_comment(comment, clause, no_comments)
                dml_repeat = True

            # INT4(expr) => expr::INTEGER
            result = int4_regex.match(sql)
            if result:
                pre = result.group(1)
                clause = result.group(2)
                col = result.group(3)
                post = result.group(4)
                sql = '{0} {3}::integer {1}'.format(pre, post, clause, col)
                comment = append_comment(comment, clause, no_comments)
                dml_repeat = True

        # write out possibly modified line
        sqlout.write(sql)
        if comment:
            sqlout.write('\t\t-- {0}'.format(comment))
        sqlout.write('\n')
        continue


def append_comment(old_comment, new_comment, no_comments):
    if no_comments:
        return None
    if old_comment and new_comment:
        return '{0} // {1}'.format(old_comment, new_comment)
    if not old_comment:
        return new_comment
    return old_comment


##### MAIN #####
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert SQL dialects to Snowflake.')
    parser.add_argument('--no_comments', action='store_true',
                        help='suppress comments with changes (default: show changes)')
    parser.add_argument('inputfile', action='store', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                        help='input SQL file in other-vendor dialect (default: stdin)')
    parser.add_argument('outputfile', action='store', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help='output SQL file in Snowflake dialect (default: stdout)')
    args = parser.parse_args();
    print(sys.stderr, "no_comments = " + str(args.no_comments))
    print(sys.stderr, "input: " + str(args.inputfile.name))
    print(sys.stderr, "output: " + str(args.outputfile.name))

    # with etl_utils.error_reporting():
    make_snow(args.inputfile, args.outputfile, args.no_comments)
    args.inputfile.close()
    args.outputfile.close()
    print(sys.stderr, "done translating " + args.inputfile.name)
