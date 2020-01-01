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
	OHEADER = ['Date', 'Description', 'Category', 'Note', 'S', '%', 'Cash', 'Amount', 'Split']
	ODATE = 0
	ODESCRIPTION = 1
	OCATEGORY = 2
	ONote = 3
	OSHARED = 4
	OBONUS_PERCENT = 5
	OBONUS_AMOUNT = 6
	OAMOUNT = 7
	OSPLIT = 8

	# Pattern for a percentage
	PERCENT_PAT = re.compile("(-?)(\\d+)\\%")

	# Pattern for a dollar amount
	AMOUNT_PAT = re.compile("(-?)\\$(\\d+\\.\\d+)")
	
	# Pattern for a date
	DATE_PAT = re.compile("^\\d{2}/\\d{2}/\\d{4}$")



	def __init__(self, negate_amount=False):
		# A list of output rows parsed from last statement.
		self.statement = []
		self.debug = 1
		self.negate_amount = negate_amount



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
			
			
	def _parse_amount(self, p, negate_amount=False):
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
		if negate_amount:
			v = -v
		return v
			


	def _parse_row(self, irow):
		'''Parse a single input row, producing an output row
		and append that to our statement.'''
		orow = []
		orow.append(irow[self.IDATE])
		orow.append(irow[self.IDESCRIPTION])
		orow.append("")		# Note
		orow.append("")		# Category
		orow.append("")		# Shared
		orow.append(self._parse_percent(irow[self.IBONUS_PERCENT]))
		orow.append(self._parse_amount(irow[self.IBONUS_AMOUNT]))
		orow.append(self._parse_amount(irow[self.IAMOUNT], negate_amount=self.negate_amount))
		orow.append("")		# Split
		self.statement.append(orow)



	def _parse_transaction_table(self, table_number, transactions, startIndex):
		'''Parse transactions from table 

		Parameters:
			table_number - Table we are parsing
			transactions - Table data
			startIndex - Index of first transaction to parse

		Returns:
			(txCount, i) - Number of transactions parsed and the index of one beyond last row parsed.
		'''
		i = startIndex
		txCount = 0
		while i < len(transactions):
			row = transactions[i]
			if self.DATE_PAT.match(row[0]):
				self._parse_row(row)
				txCount += 1
				if i+1 < len(transactions) and transactions[i+1][self.IDCA] == "Daily Cash Adjustment":
					# Refunds cause a dailly cash adjustment as a charge to the apple card
					# Same date as previous transaction
					i += 1
					adj_row = transactions[i]
					adj_row[0] = row[0]
					self._parse_row(adj_row)
			else:
				print ("  {}:    Skipping '{}'".format(table_number, row[0]))
			i += 1
		return (txCount, i)



	def _parse_table(self, table_number, table):
		'''Parse a table.  

		Parameters:
			table_number - the table we are parsing
			table - Table data

		Returns:
			Number of transactions parsed. 

		'''
		txCount = 0
		if len(table.data) < 3:
			print ("  {}:  too short".format(table_number))
			return txCount

		#
		# Search table for header that indicates beginning of transactions
		# Only look onces until transactions are found and assume remainder of table
		# contains data. 
		#
		extractAt = -1
		for ri in range(0,len(table.data)-2):
			if len(table.data[ri]) >= 1 and table.data[ri][0] == 'Transactions':
				if len(table.data[ri+1]) == 5 and table.data[ri+1] == ["Date","Description","Daily Cash","","Amount"]:
					extractAt = ri
					break
			# print ("  {}:  Skip row {}: {}".format(table_number, ri, ",".join(table.data[ri])))

		# 
		# Headers found, parse at first data row.
		#
		if extractAt >= 0:
			print ("  {}:  Extract row {}: {}".format(table_number, extractAt+1, ",".join(table.data[extractAt+1])))
			(txCount, endAt) = self._parse_transaction_table(table_number, table.data, extractAt+2)
			print ("  {}:  {} Transactions, End at row {}:  {}".format(table_number, txCount, endAt, 
					"(last)" if endAt == len(table.data) else ",".join(table.data[extractAt+1])))
		return txCount
   


	def parse(self, infile):
		txCount = 0
		self.statement = []
		tables = camelot.read_pdf(infile
				, pages='2-end'
				, flavor='stream'
				#, process_background=True
				)
		table_number = 0
		if self.debug >= 1: print ("Tables:  {}".format(len(tables)))
		for table in tables:
			tc = self._parse_table(table_number, table)
			table_number += 1
			txCount += tc
		print ("{} transactions".format(txCount))


	def write(self, outfile):
		with open(outfile, 'w', newline='', encoding='utf8') as fd:
			writer = csv.writer(fd)
			writer.writerow(self.OHEADER)
			writer.writerows(self.statement)


def dump_tables(infile, outfile):
	tables = camelot.read_pdf(infile
				, pages='2-end'
				, flavor='stream'
				#, process_background=True
				)
	(n,e) = os.path.splitext(outfile)
	table_number = 0
	for table in tables:
		of = "{}_{}.csv".format(n,table_number,e)
		table.to_csv(of)
		table_number += 1


parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
	description='''Parse apple card statement.''')


parser.add_argument('-c', action='store_true', help='Dump all tables to csv files')
parser.add_argument('-n', action='store_true', help='Negate amounts (make expenses negative values)')
parser.add_argument('infile', help='Input file (.pdf)')
parser.add_argument('outfile', help='Output file (.csv).')


args = parser.parse_args()

if args.c:
	dump_tables(args.infile, args.outfile)
else:
	statement_parser = AppleStatementParser(negate_amount=args.n)
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

