# Squid: S-syntax - Quick 'n Dirty
# --------------------------------
# By Sathaporn (Hubert) Hu 2014

# Q: What is Squid?
# A: It is a preprocessor that allows S-syntax macros to be used in codes
#    written in many programming languages. To use Squid, give it a rule file,
#    a file that you want to preprocess and voila!

# Q: Many programming languages? What kind of programming languages?
# A: Squid should work on programming languages that are not dependent on space.
#    So even though Squid is written in Python, it doesn't work quite well on
#    Python since it cannot expand a macro into multiline codes in the language.

# Q: How to set up a rule file?
# A: It's simple. Look at this example:
#    (def-frag (f x y z) `{F( x , y ) + G( y , z ) - H( z, y )})
#    
#    def-frag: tells that this is a rule.
#    (f x y z): form of the macro.
#    `{F( x , y ) + G( y , z ) - H( z, y )}: What the form will be expanded to.
#
#    Note that the arguments x, y, z are isolated with space in `{}. Without
#    the spaces, your rule will not work! This is quick 'n dirty after all!

# Q: How do I use the macro?
# A: Simply write embed the S-syntax into the code. So you can aim for something
#    like this:
#    
#    function test() {
#        if ((f 10 20 30) == 40)
#            alert("That's numberwang!");
#        else
#            alert("That's not a numberwang! Rotate the board!");

# Q: Wait, isn't the rule similar to C's #define
# A: Absoultely, and it is in fact inspired by that.

# Q: I'm very stoked. And I want to deploy this on my multimillion dollars IT
#    project!
# A: Please don't. I've only tested with one rule and one file so far. 'quick 'n
#    dirty' should also implies that it shouldn't be used in productive setting.
#    Hopefully, I can create Squic (S-syntax: Quick and Clean), but I'm not
#    promising anything.

import sys

## Rule Generation ##

# This part contains codes pertaining to parse a rule file.

class Rule:
    '''The rule for transformation.'''
    
    def __init__ (self, args, exp_context):
        self.args = args
        self.exp_context = exp_context
        
def process_rules(rule_text):
    '''Process the given rule and return a list of processed lines.'''

    processed_text = []
    paren_val = 0
    
    comment_mode = False
    
    buf = ""
    for c in rule_text:

        # Check to see if the current character is in a comment or not.
        if comment_mode:
            # If so, check for newline character.
            comment_mode = (c != "\n")
        else:
            # Otherwise, process the next characters as code.
            
            if c == "/": # If there is a comment character, turn to comment mode.
                comment_mode = True
            else:
                buf += c
                
                # Check for parenthesis balance.
                if c == "(":
                    paren_val += 1
                elif c == ")":
                    paren_val -= 1
                    
                    if paren_val == 0:
                        processed_text.append(buf)
                        buf = ""
                    elif paren_val < 0:
                        print("Preprocessor error!")
                        sys.exit()
                        
    i = 0
    while i < len(processed_text):
        processed_text[i] = processed_text[i].strip()
        i += 1

    return processed_text

def gen_rules(processed_text):
    '''Generate the rules to be used for the code.'''

    rules = {}
    
    for t in processed_text:
        t_split = t.split("`")
        exp_context = t_split[1][1:-2]
        t_split_left = t_split[0].strip().split(" ")
        
        if (t_split_left[0] != "(def-frag"):
            print("Preprocessor error!")
            sys.exit()
        
        rule_name = t_split_left[1][1:]
        args = t_split_left[2:]
        args[-1] = args[-1][:-1]

        # print(rule_name, args, exp_context)
        
        rules[rule_name] = Rule(args, exp_context)
        
    return rules

## This part is for preprocessing the code ##

def gen_clause(clause):
    '''Receive a string clause and turns it into a list which is easier to deal
       with.'''
    
    arg_left_i = 0
    arg_right_i = 0
    paren_val = 0
    args = []
    arg = ""
    
    clause_formatted = clause[1:-1].strip()
    quote_mode = False
    
    i = 0
    while i < len(clause_formatted):
        if not quote_mode:
            if clause_formatted[i] == "(":
                paren_val += 1
                arg += "("
            elif clause_formatted[i] == ")":
                paren_val -= 1
                arg += ")"
            elif clause_formatted[i] == " ":
                if paren_val == 0:
                    args.append(arg)
                    arg = ""
                else:
                    arg += clause_formatted[i]
            elif clause_formatted[i] == '"':
                quote_mode = True
                arg += '"'
            else:
                arg += clause_formatted[i]
        else:
            if clause_formatted[i] == '"':
                quote_mode = False
                arg += '"'
            else:
                arg += clause_formatted[i]
        
        i += 1
    
    args.append(arg) # There is still one more argument in the pipeline!
    return args

def expand_clause(rules, clause):
    '''Expand a clause with the given rule and argument.'''

    # Check if the clause matches any rule. If it doesn't match, then don't
    # expand it!
    
    rule = None
    
    for r in rules:
        if r == clause[0]:
            rule = rules[r]
    
    if rule == None:
        cat = ""
        for c in clause:
            cat += c + " "
        return "(" + cat[:-1] + ")"
    
    # If it matches with a rule, expand it by comparing with the expansion
    # context.

    fragment = rule.exp_context.split()
    
    if len(rule.args) == len(clause[1:]):
        i = 0
        while i < len(rule.args):
            j = 0
            while j < len(fragment):
                # If the pattern matches, perform the substitution!
                if fragment[j] == rule.args[i]:
                    fragment[j] = clause[i+1]
                j += 1
            i += 1
    
    combined = ""
    
    # Combining everything.
    
    for f in fragment:
        # If the fragment is a clause itself, then recursively expand it.
        if f[0] == "(" and f[-1] == ")":
            combined += expand_clause(rules, gen_clause(f))
        else:
            combined += f + " "
    
    return combined[:-1]

def expand(rules, code):
    '''Expand the given code. This is the bonafide function for expanding a 
       code.'''

    # Set up the helpful variables.
    
    paren_left_i = 0
    i = 0
    paren_val = 0
    buf = ""
    output = ""
    
    # Traverse the code. If a clause is found, expand it. 
    
    while i < len(code):
        if code[i] == "(":
            paren_val += 1
            buf += "("

            if paren_left_i == 0:
                paren_left_i = i
            
            i += 1
        elif code[i] == ")":
            paren_val -= 1
            buf += ")"
            
            if paren_val == 0:
                # The expansion begins!
                clause = gen_clause(buf)
                exp = expand_clause(rules, clause)
                output += exp
                i += 1
                
                buf = ""
            else:
                i += 1
        else:
            if paren_val > 0: # Inside a clause
                buf += code[i]
            else:
                output += code[i]
            i += 1
            
    return output

## The program starts here #####################################################

if __name__ == "__main__":
  
    # There are multiple ways to do I/O. Change to what's good for you.
  
    rule_data_file = open(input("Rule file path: "), 'r')
    code_in_file = open(input("Code file path: "), 'r')

    rule_data = rule_data_file.read()
    rule_data_file.close()
    
    code = code_in_file.read()
    code_in_file.close()
    
    rules = gen_rules(process_rules(rule_data))
    exp_code = expand(rules, code)
    
    code_out_file = open(input("Output file path: "), 'w')
    code_out_file.write(exp_code)
    code_out_file.close()
    
    ## Some ancient testing code ##
    
    #rule_data = """(def-frag (f x y) `(if F( x ) y ; ! y ;))
    #(def-frag (g x y z w) `(G( x w ( z ( w ())));)) 

    # Generate the rules
    #rules = gen_rules(process_rules(rule_data))
    
    #print(gen_clause("(f x y)"))
    #print(gen_clause("(f (g x y z) w a b)"))
    #print(expand(rules, "(f a b)"))
    #print(expand(rules, "(g A B C D)"))