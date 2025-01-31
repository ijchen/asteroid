###########################################################################################
# Asteroid interpreter
#
# (c) University of Rhode Island
###########################################################################################

import os
import sys

from asteroid.globals import *
from asteroid.support import *
from asteroid.frontend import Parser
from asteroid.state import state, dump_trace
from asteroid.walk import walk_program, debug_walk

# the prologue file is expected to be in the 'modules' folder
prologue_name = 'prologue.ast'
def load_prologue():
    """
    Load the prolog files and run them.
    """
    prologue_file = ''
    prologue_file_base = os.path.join('modules', prologue_name)
    module_path = os.path.join(os.path.split(os.path.abspath(__file__))[0], prologue_file_base)
    working_path = os.path.join(os.getcwd(), prologue_file_base)

    if os.path.isfile(module_path):
        prologue_file = module_path
    
    elif os.path.isfile(working_path):
        prologue_file = working_path
    
    else:
        raise ValueError("Asteroid prologue '{}' not found"
                        .format(prologue_file_base))
    
    with open(prologue_file) as f:
        state.modules.append(prologue_name)
        data = f.read()
        pparser = Parser(prologue_file)
        (LIST, pstmts) = pparser.parse(data)

    state.AST = ('list', pstmts)
    walk_program(state.AST)
    state.AST = None

def interp(program,
           program_name = "<input>",
           tree_dump=False,
           do_walk=True,
           symtab_dump=False,
           exceptions=False,
           redundancy=True,
           prologue=True,
           debugger=None,
           functional_mode=False,
           initialize_state = True
           ):
    '''
    The function 'interp' is the top-level entry point to the
    Asteroid interpreter with the following arguments:
      * program: a string representing an Asteroid program
      * program_name: the of the program to be interpreted
      * tree_dump: a flag indicating whether the AST should be dumped after parsing
      * do_walk: a flag indicating whether the interpret should interpret the AST
      * symtab_dump: a flag indicating whether the contents of the symbol
                     table should be printed out
      * exceptions: when true Python style exceptions are shown, otherwise
                    Asteroid style exceptions are shown
      * redundancy: a flag indicating whether the function pattern checker should be run
      * prologue: a flag indicating whether the Asteroid prologue file should be loaded
      * functional_mode: if set then the Asteroid interpreter behaves like an interpreter
                         functional programming language.
      * initialize_state: if set then the interpreter will (re)initialize its state.  
    '''
    try:
        # initialize state
        if initialize_state:
            state.initialize(program_name)

        if prologue:
            load_prologue()

        # initialize "check for useless clauses" flag
        state.eval_redundancy = redundancy

        # build the AST
        parser = Parser(program_name, functional_mode)
        (LIST, istmts) = parser.parse(program)
        state.AST = ('list', istmts)

        # walk the AST
        if tree_dump:
            dump_AST(state.AST)
        if do_walk:
            if debugger:
                debug_walk(state.AST, debugger)
            else:
                walk_program(state.AST)
        if symtab_dump:
            state.symbol_table.dump()

    # Note: all exceptions generated by Asteroid should go through the handler
    #       for 'Exception' unless the exception needs special handling like
    #       'ThrowValue' or 'ReturnValue' etc.
    except ThrowValue as throw_val:
        dump_trace()
        # handle exceptions using the standard Error constructor
        module, lineno = state.lineinfo
        if throw_val.value[0] == 'apply' and throw_val.value[1][1] == 'Error':
            (APPLY, (ID, id), (APPLY, error_obj, rest)) = throw_val.value
            print("error: {}: {}: {}".format(module, lineno, term2string(error_obj)))
        else:
            print("error: {}: {}: unhandled Asteroid exception: {}"
                  .format(module, lineno, term2string(throw_val.value)))
        # needed for REPL
        if not exceptions:
            sys.exit(1)

    except ReturnValue as inst:
        dump_trace()
        module, lineno = state.lineinfo
        print("error: {}: {}: return statement used outside a function environment"
              .format(module, lineno))
        # needed for REPL
        if not exceptions:
            sys.exit(1)

    except  KeyboardInterrupt as e:
        if debugger:
            raise e

        dump_trace()
        print("error: keyboard interrupt")
        # needed for REPL
        if not exceptions:
            sys.exit(1)

    except SystemExit:
        exit(0)

    except Exception as e:
        if exceptions: # rethrow the exception so that you can see the full backtrace
            if symtab_dump:
                state.symbol_table.dump()
            raise e
        else:
            dump_trace()
            module, lineno = state.lineinfo
            print("error: {}: {}: {}".format(module, lineno, e))
            # needed for REPL
            if not exceptions:
                sys.exit(1)

    except BaseException as e:
        dump_trace()
        print("error: {}".format(e))
        # needed for REPL
        if not exceptions:
            sys.exit(1)