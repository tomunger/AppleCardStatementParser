'''
Parse an apple card statement to CSV file.
'''

import sys
import os
import traceback
import camelot
import csv
import argparse
import re



class ParseException(Exception):
	pass


class AppleStatementParser(object):
	'''Apple card statement parser.'''


	# Statement columns
	IDATE = 0
	IDESCRIPTION = 1
	IBONUS_PERCENT = 2
	IBONUS_AMOUNT = 3
	IAMOUNT = 4

	# Input daily cash adjustment columns.  Appears after a return.
	IDCA = 1
	IDCA_PERCENT = 2
	IDCA_AMOUNT = 4

	# Output file columns
	OHEADER = ['Date', 'Description', 'Category', 'Shared', 'BP', 'BA', 'Amount']
	ODATE = 0
	ODESCRIPTION = 1
	OCATEGORY = 2
	OSHARED = 3
	OBONUS_PERCENT = 4
	OBONUS_AMOUNT = 5
	OAMOUNT = 6

	# Pattern for a percentage
	PERCENT_PAT = re.compile("(-?)(\\d+)\\%")

	# Pattern for a dollar amount
	AMOUNT_PAT = re.compile("(-?)\\$(\\d+\\.\\d+)")
	
	# Pattern for a date
	DATE_PAT = re.compile("^\\d{2}/\\d{2}/\\d{4}$")



	def __init__(self):
		# A list of output rows parsed from last statement.
		self.statement = []
		self.debug = 1



	def _parse_percent(self, p):
		if not p:
			return 0.0
		m = self.PERCENT_PAT.match(p)
		if m is None:
			raise ParseException("Invalid percentage string '{}'".format(p))
		v = m.group(2)
		try:
			v = int(v)
		except:
			raise ParseException("Invalid percentage value '{}'".format(p))
		if m.group(1) == '-':
			v = -v
		return v/100.0
			
			
	def _parse_amount(self, p):
		if not p:
			return 0.0
		m = self.AMOUNT_PAT.match(p)
		if m is None:
			raise ParseException("Invalid amount string '{}'".format(p))
		try:
			v = float(m.group(2))
		except:
			raise ParseException("Invalid amount value '{}'".format(p))
		if m.group(1) == '-':
			v = -v
		return v
			


	def _parse_row(self, irow):
		orow = []
		orow.append(irow[self.IDATE])
		orow.append(irow[self.IDESCRIPTION])
		orow.append("")
		orow.append("")
		orow.append(self._parse_percent(irow[self.IBONUS_PERCENT]))
		orow.append(self._parse_amount(irow[self.IBONUS_AMOUNT]))
		orow.append(self._parse_amount(irow[self.IAMOUNT]))
		self.statement.append(orow)



	def _parse_transaction_table(self, transactions):
		i = 0
		while i < len(transactions):
			row = transactions[i]
			if self.DATE_PAT.match(row[0]):
				self._parse_row(row)
				if i+1 < len(transactions) and transactions[i+1][self.IDCA] == "Daily Cash Adjustment":
					# Refunds cause a dailly cash adjustment as a charge to the apple card
					# Same date as previous transaction
					i += 1
					adj_row = transactions[i]
					adj_row[0] = row[0]
					self._parse_row(adj_row)
			else:
				print ("    Skipping '{}'".format(row[0]))
			i += 1



	def _parse_table(self, table, table_count):
		if len(table.data) < 3:
			print ("  {}:  too short".format(table_count))
			return
		if len(table.data[0]) < 1 or table.data[0][0] != 'Transactions':
			print ("  {}:  First header does not contain 'Transactions'".format(table_count))
			return
		if len(table.data[1]) < 5 or table.data[1] != ["Date","Description","Daily Cash","","Amount"]:
			print ("  {}:  Second header does not column names".format(table_count))
			return
		print ("  {}:  Transaction table".format(table_count))
		self._parse_transaction_table(table.data[2:])

   


	def parse(self, infile):
		self.statement = []
		tables = camelot.read_pdf('local-pdf/apple card 2019-09.pdf'
				, pages='2-end'
				, flavor='stream'
				#, process_background=True
				)
		i = 0
		if self.debug >= 1: print ("Tables:  {}".format(len(tables)))
		for table in tables:
			self._parse_table(table, i)
			i += 1


	def write(self, outfile):
		with open(outfile, 'w', newline='', encoding='utf8') as fd:
			writer = csv.writer(fd)
			writer.writerow(self.OHEADER)
			writer.writerows(self.statement)


def dump_tables(infile, outfile):
	tables = camelot.read_pdf('local-pdf/apple card 2019-09.pdf'
				, pages='2-end'
				, flavor='stream'
				#, process_background=True
				)
	(n,e) = os.path.splitext(outfile)
	i = 0
	for table in tables:
		of = "{}_{}.csv".format(n,i,e)
		table.to_csv(of)
		i += 1


parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
	description='''Parse apple card statement.''')


parser.add_argument('-c', action='store_true', help='Dump to csv fils')
parser.add_argument('infile', help='Input file (.pdf)')
parser.add_argument('outfile', help='Output file (.csv).')


args = parser.parse_args()

if args.c:
	dump_tables(args.infile, args.outfile)
else:
	statement_parser = AppleStatementParser()
	try:
		statement_parser.parse(args.infile)
	except ParseException as e:
		print (e.message)
		sys.exit(-1)
	except Exception as e:
		print (e)
		traceback.print_exc()
		sys.exit(-2)
	statement_parser.write(args.outfile)

