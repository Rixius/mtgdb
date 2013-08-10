import urllib2		#import url getter library

#list of certain sections in the html that are important
section_lookup = ['_nameRow"', '_manaRow"', '_cmcRow"', '_typeRow"', '_ptRow"']

#empty string variables to pass to the functions - not sure I actually needs these with the way it really works
#these were here so I could return them, but I don't think I need to do that
card_value = ""
mana_cost = ""
card_name = ""
card_type = ""
main_type = ""
subtype = ""
card_text = ""
rarity = ""
card_set = ""
power_toughness = ""

#looks for info between certain tags using the section_lookup to start from
def get_info_after_value(block, card_value_read, card_value):
	read_start = block.find(card_value_read)
	card_value_start = block.find('ue">', read_start) + 4
	card_value_end = block.find('</div>', card_value_start)
	card_value = block[card_value_start:card_value_end]
	card_value = card_value.strip()
	return card_value

#gets the mana cost and formats it into single letter cost labels for colors
def get_mana_cost(block, mana_cost_read, mana_cost_end, mana_cost):
	mana_start = block.find(mana_cost_read)
	mana_end = block.find(mana_cost_end)
	mana_cost_start = block.find("alt=", mana_start) + 5
	mana_cost_stop = block.find('"', mana_cost_start)
	mana_cost = block[mana_cost_start:mana_cost_stop]
	str_cost = str(mana_cost)	
	if len(str_cost) != 2:								#looks for 2 digit cost, if it is, do nothing
		if str_cost == 'Blue':							#if not 2 digit, check for 'Blue' and change it
			mana_cost = 'U'
		elif str_cost == 'Variable Colorless':			#checks for X casting cost, and makes it X
			mana_cost = 'X'
		elif str_cost.find(' or ') != -1:
			or_pos_start = str_cost.find(' ')
			or_pos_end = str_cost.find(' or ') + 4
			if str_cost[:or_pos_start] == 'Blue':
				first_color = 'U'
				second_color = str_cost[or_pos_end:or_pos_end + 1]
			elif str_cost[or_pos_end:] == 'Blue':
				first_color = str_cost[0]
				second_color = 'U'
			else:
				first_color = str_cost[0]
				second_color = str_cost[or_pos_end:or_pos_end + 1]
			mana_cost = first_color + '/' + second_color
			# Azor's Elocutors 265418 White/Blue
			# Blistercoil Weird 289222 Blue/Red
		else:
			mana_cost = str_cost[0]						#otherwise take the first character of the cost
	else:
		mana_cost = str_cost							#gets set as a string version of a two digit casting cost to be concatted with strings later
	while block.find('alt="', mana_cost_stop) < mana_end:
		mana_cost_start = block.find("alt=", mana_cost_stop) + 5
		mana_cost_stop = block.find('"', mana_cost_start)
		next_mana_cost = block[mana_cost_start:mana_cost_stop]
		if next_mana_cost == 'Blue':
			next_mana_cost = 'U'
		elif next_mana_cost == 'Variable Colorless':
			next_mana_cost = 'X'
		elif next_mana_cost.find(' or ') != -1:
			or_pos_start = next_mana_cost.find(' ')
			or_pos_end = next_mana_cost.find(' or ') + 4
			if next_mana_cost[:or_pos_start] == 'Blue':
				first_color = 'U'
				second_color = next_mana_cost[or_pos_end:or_pos_end + 1]
			elif next_mana_cost[or_pos_end:] == 'Blue':
				first_color = next_mana_cost[0]
				second_color = 'U'
			else:
				first_color = next_mana_cost[0]
				second_color = next_mana_cost[or_pos_end:or_pos_end + 1]
			next_mana_cost = ' ' + first_color + '/' + second_color
		else:
			next_mana_cost = next_mana_cost[0]
		mana_cost += next_mana_cost
	return mana_cost

#takes the card type and splits it into the main type and subtype, strips everything else off
def fix_card_type(card_type, main_type, subtype):
	main_type_end = card_type.find("\xe2")
	if main_type_end == -1:
		subtype = ""
		main_type = card_type
		return main_type, subtype
	main_type = card_type[:main_type_end].strip()
	subtype_start = main_type_end + 3
	subtype = card_type[subtype_start:].strip()
	return main_type, subtype
	
#cycles through the card text group looking for multiple sections of it; does not capture flavor text
def get_card_text(block, card_text, text_area_end):
	text_block_start = block.find('Card Text:')								#start of the card text area
	if text_block_start == -1:												#check to see if there's any text
		card_text = ""
		return card_text
	if block.find('_markRow', text_block_start) != -1:						#searches for a Watermark area so as to not capture it as part of the card text
		text_block_end = block.find('_markRow', text_block_start)
	else:
		text_block_end = block.find(text_area_end)							#end of the card text area
	text_start = block.find('cardtextbox">', text_block_start) + 13			#search for the first occurrence of card text, add enough to to get to the beginning
	text_stop = block.find('</div>', text_start)							#search for the end of the card text
	card_text = block[text_start:text_stop]									#get the actual text
	while block.find('cardtextbox">', text_stop) < text_block_end:			#loop to check for more occurrences of card text
		if block.find('cardtextbox">', text_stop) == -1:
			return card_text
		text_start = block.find('cardtextbox">', text_stop) + 13			#set new start point to get text
		text_stop = block.find('</div>', text_start)						#set new stop point for text, searching from start point
		combine_with_breaks = "<br /><br />" + block[text_start:text_stop] 	#combine html breaks with actual card text
		card_text += combine_with_breaks									#combine html break added text with existing captured card text
	return card_text														#once done, return combined card text

#gets the rarity of the card alone with the card set - combined into one function because it was easy
def get_rarity_and_set(block, rarity, card_set):
	rarity_pos = block.find("rarity=") + 7
	rarity = block[rarity_pos:rarity_pos + 1]
	card_set_start = block.find('alt="', rarity_pos) + 5
	card_set_end = block.find('(', card_set_start)
	card_set = block[card_set_start:card_set_end]
	return rarity, card_set
	
#gets power and toughness, pretty simple
def get_power_toughness(block,power_toughness):
	pt_read = block.find("P/T:")
	if pt_read == -1:
		return
	pt_start = block.find('ue">', pt_read) + 4
	pt_end = block.find('</div>', pt_start)
	power_toughness = block[pt_start:pt_end].strip()
	return power_toughness

#this runs all the functions, passes what needs to be passed to them, sends things to get fixed, and returns all the info as a tuple
def parse_the_info(block, card_value, card_name, mana_cost, card_type, main_type, subtype, card_text, rarity, card_set, power_toughness):
	card_name = get_info_after_value(block, section_lookup[0], card_value)
	mana_cost = get_mana_cost(block, section_lookup[1], section_lookup[2], card_value)
	card_type = get_info_after_value(block, section_lookup[3], card_value)
	main_type, subtype = fix_card_type(card_type, main_type, subtype)
	card_text = get_card_text(block, card_text, section_lookup[4])
	rarity, card_set = get_rarity_and_set(block,rarity, card_set)
	power_toughness = get_power_toughness(block, power_toughness)
	return card_name, mana_cost, main_type, subtype, card_text, card_set, rarity, power_toughness

#main function - initializes where the card ids start, connects to the db, then loops through all the web urls
#inserting the card ID as it goes through
def getCardInfo(cardID):	
	strCardID = str(cardID)
	website = urllib2.urlopen("http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid=" + strCardID)
	website_html = website.read()
	search_start = website_html.find("smallGreyMono") + 1
	block_start = website_html.find("smallGreyMono", search_start)
	block = website_html[block_start:]
	card = parse_the_info(block, card_value, card_name, mana_cost, card_type, main_type, subtype, card_text, rarity, card_set, power_toughness)
	card_list = list(card)
	card_list.insert(0, cardID)
	return card_list

print "Run getCardInfo() and pass in the card ID of the card you want"
	
#results are card_list[Card ID, Card Name, Casting Cost, Main Type, Subtype, Card Text, Card Set, Rarity, Power/Toughness]