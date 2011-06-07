#!/usr/local/bin/python
'''
pyMIDACO - A Python pyOpt interface to MIDACO. 

Copyright (c) 2008-2011 by pyOpt Developers
All rights reserved.
Revision: 1.0   $Date: 05/12/2009 21:00$


Tested on:
---------
Linux with gfortran
Linux with pathf95
Win32 with gfortran
Mac with g95

Developers:
-----------
- Dr. Ruben E. Perez (RP)

History
-------
	v. 1.0	- Initial Class Creation (RP, 2009)
'''

__version__ = '$Revision: $'

'''
To Do:
	- 
'''

# =============================================================================
# MIDACO Library
# =============================================================================
try:
	import midaco
except:
	raise ImportError('MIDACO shared library failed to import')
#end

# =============================================================================
# Standard Python modules
# =============================================================================
import os, sys
import copy, time

# =============================================================================
# External Python modules
# =============================================================================
import numpy

# =============================================================================
# Extension modules
# =============================================================================
from pyOpt import Optimizer
from pyOpt import History

# =============================================================================
# Misc Definitions
# =============================================================================
inf = 10.E+20  # define a value for infinity
# =============================================================================
eps = 1.0	# define a value for machine precision
while ((eps/2.0 + 1.0) > 1.0):
	eps = eps/2.0
#end
eps = 2.0*eps
#eps = math.ldexp(1,-52)


# =============================================================================
# MIDACO Optimizer Class
# =============================================================================
class MIDACO(Optimizer):
	
	'''
	MIDACO Optimizer Class - Inherited from Optimizer Abstract Class
	'''
	
	def __init__(self, pll_type=None, *args, **kwargs):
		
		'''
		MIDACO Optimizer Class Initialization
		
		**Keyword arguments:**
		
		- pll_type -> STR: Parallel Implementation (None, 'POA'-Parallel Objective Analysis), *Default* = None
		
		Documentation last updated:  Feb. 16, 2010 - Peter W. Jansen
		'''
		
		#
		if (pll_type == None):
			self.poa = False
		elif (pll_type.upper() == 'POA'):
			self.poa = True
		else:
			raise ValueError("pll_type must be either None or 'POA'")
		#end
		
		#
		name = 'MIDACO'
		category = 'Global Optimizer'
		def_opts = {
		# MIDACO Options
		'ACC':[float,0.0001],		# Accuracy for constraint violation
		'ISEED':[int,-1],			# Seed for random number generator  (e.g. ISEED = 0,1,2,3,...)
		'QSTART':[int,0],			# Quality of starting point (0 - if x0 is a random point)
		'MAXEVAL':[int,500000],		# Maximal function evaluations
		'MAXTIME':[float,86400],	# Maximal time limit, in seconds
		'IPRINT':[int,1],			# Output Level (<0 - None, 0 - Screen, 1 - File)
		'IOUT':[int,6],				# Output Unit Number
		'IFILE':[str,'MIDACO.out'],	# Output File Name
		}
		informs = {
		0 : '', 
		1 : '',
		}
		Optimizer.__init__(self, name, category, def_opts, informs, *args, **kwargs)
		
		
	def __solve__(self, opt_problem={}, store_sol=True, disp_opts=False, store_hst=False, hot_start=False, *args, **kwargs):
		
		'''
		Run Optimizer (Optimize Routine)
		
		**Keyword arguments:**
		
		- opt_problem -> INST: Optimization instance
		- store_sol -> BOOL: Store solution in Optimization class flag, *Default* = True 
		- disp_opts -> BOOL: Flag to display options in solution text, *Default* = False
		- store_hst -> BOOL/STR: Flag/filename to store optimization history, *Default* = False
		- hot_start -> BOOL/STR: Flag/filename to read optimization history, *Default* = False
		
		Additional arguments and keyword arguments are passed to the objective function call.
		
		Documentation last updated:  February. 17, 2011 - Peter W. Jansen
		'''
		#
		if self.poa:
			try:
				import mpi4py
				from mpi4py import MPI
			except ImportError:
				print 'pyMIDACO: Parallel objective Function Analysis requires mpi4py'
			#end
			comm = MPI.COMM_WORLD
			nproc = comm.Get_size()
			if (mpi4py.__version__[0] == '0'):
				Bcast = comm.Bcast
			elif (mpi4py.__version__[0] == '1'):
				Bcast = comm.bcast
			#end
			self.pll = True
			self.myrank = comm.Get_rank()
		else:
			self.pll = False
			self.myrank = 0
		#end
		
		myrank = self.myrank
		
		# 
		tmp_file = False
		def_fname = self.options['IFILE'][1].split('.')[0]
		if isinstance(store_hst,str):
			if isinstance(hot_start,str):
				if (myrank == 0):
					if (store_hst == hot_start):
						hos_file = History(hot_start, 'r', self)
						log_file = History(store_hst+'_tmp', 'w', self, opt_problem.name)
						tmp_file = True
					else:
						hos_file = History(hot_start, 'r', self)
						log_file = History(store_hst, 'w', self, opt_problem.name)
					#end
				#end
				self.sto_hst = True
				self.h_start = True
			elif hot_start:
				if (myrank == 0):
					hos_file = History(store_hst, 'r', self)
					log_file = History(store_hst+'_tmp', 'w', self, opt_problem.name)
					tmp_file = True
				#end
				self.sto_hst = True
				self.h_start = True
			else:
				if (myrank == 0):
					log_file = History(store_hst, 'w', self, opt_problem.name)
				#end
				self.sto_hst = True
				self.h_start = False
			#end
		elif store_hst:
			if isinstance(hot_start,str):
				if (hot_start == def_fname):
					if (myrank == 0):
						hos_file = History(hot_start, 'r', self)
						log_file = History(def_fname+'_tmp', 'w', self, opt_problem.name)
						tmp_file = True
					#end
				else:
					if (myrank == 0):
						hos_file = History(hot_start, 'r', self)
						log_file = History(def_fname, 'w', self, opt_problem.name)
					#end
				#end
				self.sto_hst = True
				self.h_start = True
			elif hot_start:
				if (myrank == 0):
					hos_file = History(def_fname, 'r', self)
					log_file = History(def_fname+'_tmp', 'w', self, opt_problem.name)
					tmp_file = True
				#end
				self.sto_hst = True
				self.h_start = True
			else:
				if (myrank == 0):
					log_file = History(def_fname, 'w', self, opt_problem.name)
				#end
				self.sto_hst = True
				self.h_start = False
			#end
		else:
			self.sto_hst = False
			self.h_start = False
		#end
		
		#======================================================================
		# MIDACO - Objective/Constraint Values Function
		#======================================================================
		def objfun(n,m,x,f,g):
			
			# Variables Groups Handling
			if opt_problem.use_groups:
				xg = {}
				for group in group_ids.keys():
					if (group_ids[group][1]-group_ids[group][0] == 1):
						xg[group] = x[group_ids[group][0]]
					else:
						xg[group] = x[group_ids[group][0]:group_ids[group][1]]
					#end
				#end
				xn = xg
			else:
				xn = x
			#end
			
			# Flush Output Files
			self.flushFiles()
			
			# Evaluate User Function
			fail = 0
			if (myrank == 0):
				if self.h_start:
					[vals,hist_end] = hos_file.read(ident=['obj', 'con', 'fail'])
					if hist_end:
						self.h_start = False
						hos_file.close()
					else:
						[ff,gg,fail] = [vals['obj'][0][0],vals['con'][0],int(vals['fail'][0][0])]
					#end
				#end
			#end
			
			if self.pll:
				self.h_start = Bcast(self.h_start,root=0)
			#end
			if self.h_start and self.pll:
				[ff,gg,fail] = Bcast([ff,gg,fail],root=0)
			elif not self.h_start:	
				[ff,gg,fail] = opt_problem.obj_fun(xn, *args, **kwargs)
			#end
			
			# Store History
			if (myrank == 0):
				if self.sto_hst:
					log_file.write(x,'x')
					log_file.write(ff,'obj')
					log_file.write(gg,'con')
					log_file.write(fail,'fail')
				#end
			#end
			
			# 
			if (fail == 1):
				# Objective Assigment
				if (len(opt_problem._objectives.keys()) == 1):
					f = inf
				else:
					# Objective Assigment
					for i in xrange(len(opt_problem._objectives.keys())):
						f[i] = inf
					#end
				#end
				# Constraints Assigment
				for i in xrange(len(opt_problem._constraints.keys())):
					g[i] = inf
				#end
			else:
				# Objective Assigment
				if (len(opt_problem._objectives.keys()) == 1):
					f = ff
				else:
					for i in xrange(len(opt_problem._objectives.keys())):
						if isinstance(ff[i],complex):
							f[i] = ff[i].astype(float)
						else:
							f[i] = ff[i]
						#end
					#end
				#end
				# Constraints Assigment
				for i in xrange(len(opt_problem._constraints.keys())):
					if isinstance(gg[i],complex):
						g[i] = gg[i].astype(float)
					else:
						g[i] = gg[i]
					#end
				#end
			#end
			
			return f,g
		
		
		
		# Variables Handling
		nvar = len(opt_problem._variables.keys())
		nint = 0
		xl = []
		xu = []
		xx = []
		for key in opt_problem._variables.keys():
			if (opt_problem._variables[key].type == 'i'):
				nint += 1
			#end
			xl.append(opt_problem._variables[key].lower)
			xu.append(opt_problem._variables[key].upper)
			xx.append(opt_problem._variables[key].value)
		#end
		xl = numpy.array(xl)
		xu = numpy.array(xu)
		xx = numpy.array(xx)
		
		# Variables Groups Handling 
		if opt_problem.use_groups:
			group_ids = {}
			k = 0
			for key in opt_problem._vargroups.keys():
				group_len = len(opt_problem._vargroups[key]['ids'])
				group_ids[opt_problem._vargroups[key]['name']] = [k,k+group_len]
				k += group_len
			#end
		#end		
		
		# Constraints Handling
		ncon = len(opt_problem._constraints.keys())
		neqc = 0
		gg = []
		if ncon > 0:
			for key in opt_problem._constraints.keys():
				if opt_problem._constraints[key].type == 'e':
					neqc += 1
				#end
				gg.append(opt_problem._constraints[key].value)
			#end
		#end
		gg = numpy.array(gg)
		
		# Objective Handling
		objfunc = opt_problem.obj_fun
		nobj = len(opt_problem._objectives.keys())
		ff = []
		for key in opt_problem._objectives.keys():
			ff.append(opt_problem._objectives[key].value)
		#end
		ff = numpy.array(ff)
		
		
		# Setup argument list values
		nn = numpy.array([nvar], numpy.int)
		ni = numpy.array([nint], numpy.int)
		mm = numpy.array([ncon], numpy.int)
		me = numpy.array([neqc], numpy.int)
		acc = numpy.array([self.options['ACC'][1]], numpy.float)
		iseed = numpy.array([self.options['ISEED'][1]], numpy.int)
		if (myrank == 0):
			if (self.options['ISEED'][1] < 0) and not self.h_start:
				iseed = numpy.array([time.time()], numpy.int)
			#end
			if self.h_start:
				iseed = numpy.array([hos_file.read(-1,ident=['seed'])[0]['seed'][0][0]], numpy.int)
			#end
		#end
		if self.pll:
			iseed = Bcast(iseed, root=0)
		#end
		if self.sto_hst and (myrank == 0):
			log_file.write(iseed,'seed')
		#end
		ifail = numpy.array([0], numpy.int)
		qstart = numpy.array([self.options['QSTART'][1]], numpy.int)
		istop = numpy.array([0], numpy.int)
		if (myrank == 0):
			iprint = numpy.array([self.options['IPRINT'][1]], numpy.int)
		else:
			iprint = numpy.array([0], numpy.int)
		#end
		iout = numpy.array([self.options['IOUT'][1]], numpy.int)
		ifile = self.options['IFILE'][1]
		if (iprint >= 0):
			if os.path.isfile(ifile):
				os.remove(ifile)
			#end
		#end
		eval = numpy.array([0], numpy.int)
		maxeval = numpy.array([self.options['MAXEVAL'][1]], numpy.int)
		maxtime = numpy.array([self.options['MAXTIME'][1]], numpy.float)
		liw0 = 1000000
		liw = numpy.array([liw0], numpy.int)
		iw = numpy.zeros([liw], numpy.int)
		lrw0 = 1000000
		lrw = numpy.array([lrw0], numpy.int)
		rw = numpy.zeros([lrw], numpy.float)
		
		
		# Run MIDACO
		t0 = time.time()
		midaco.midaco_wrap(nn,ni,mm,me,xl,xu,xx,ff,gg,acc,iseed,ifail,qstart,
			istop,iprint,iout,ifile,eval,maxeval,maxtime,liw,iw,lrw,rw,objfun)
		sol_time = time.time() - t0
		
		if (myrank == 0):
			if self.sto_hst:
				log_file.close()
				if tmp_file:
					hos_file.close()
					name = hos_file.filename
					os.remove(name+'.cue')
					os.remove(name+'.bin')
					os.rename(name+'_tmp.cue',name+'.cue')
					os.rename(name+'_tmp.bin',name+'.bin')
				#end
			#end
		#end
		
		if (iprint > 0):
			midaco.closeunit(self.options['IOUT'][1])
		#end		
		
		
		# Store Results
		if store_sol:
			
			sol_name = 'MIDACO Solution to ' + opt_problem.name
			
			sol_options = copy.copy(self.options)
			if sol_options.has_key('defaults'):
				del sol_options['defaults']
			#end
			
			sol_inform = {}
			sol_inform['value'] = ifail[0]
			sol_inform['text'] = self.getInform(ifail[0])
			
			sol_evals = eval
			
			sol_vars = copy.deepcopy(opt_problem._variables)
			i = 0
			for key in sol_vars.keys():
				sol_vars[key].value = xx[i]
				i += 1
			#end
			
			sol_objs = copy.deepcopy(opt_problem._objectives)
			i = 0
			for key in sol_objs.keys():
				sol_objs[key].value = ff[i]
				i += 1
			#end
			
			if ncon > 0:
				sol_cons = copy.deepcopy(opt_problem._constraints)
				i = 0
				for key in sol_cons.keys():
					sol_cons[key].value = gg[i]
					i += 1
					if (i >= ncon):
						break
					#end
				#end
			else:
				sol_cons = {}
			#end
			
			sol_lambda = {}
			
			
			opt_problem.addSol(self.__class__.__name__, sol_name, objfunc, sol_time, 
				sol_evals, sol_inform, sol_vars, sol_objs, sol_cons, sol_options, 
				display_opts=disp_opts, Lambda=sol_lambda, 
				myrank=myrank, arguments=args, **kwargs)
			
		#end
		
		return ff, xx, ifail[0]
		
		
		
	def _on_setOption(self, name, value):
		
		'''
		Set Optimizer Option Value (Optimizer Specific Routine)
		
		Documentation last updated:  May. 07, 2008 - Ruben E. Perez
		'''
		
		pass
		
		
	def _on_getOption(self, name):
		
		'''
		Get Optimizer Option Value (Optimizer Specific Routine)
		
		Documentation last updated:  May. 07, 2008 - Ruben E. Perez
		'''
		
		pass
		
		
	def _on_getInform(self, infocode):
		
		'''
		Get Optimizer Result Information (Optimizer Specific Routine)
		
		Keyword arguments:
		-----------------
		id -> STRING: Option Name
		
		Documentation last updated:  May. 07, 2008 - Ruben E. Perez
		'''
		
		return self.informs[infocode]
		
		
	def _on_flushFiles(self):
		
		'''
		Flush the Output Files (Optimizer Specific Routine)
		
		Documentation last updated:  August. 09, 2009 - Ruben E. Perez
		'''
		
		# 
		iPrint = self.options['IPRINT'][1]
		if (iPrint >= 0):
			midaco.pyflush(self.options['IOUT'][1])
		#end
	


#==============================================================================
# MIDACO Optimizer Test
#==============================================================================
if __name__ == '__main__':
	
	# Test MIDACO
	print 'Testing ...'
	midaco = MIDACO()
	print midaco
	