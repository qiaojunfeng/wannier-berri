#------------------------------------------------------------#
# This file is distributed as part of the Wannier19 code     #
# under the terms of the GNU General Public License. See the #
# file `LICENSE' in the root directory of the Wannier19      #
# distribution, or http://www.gnu.org/copyleft/gpl.txt       #
#                                                            #
# The Wannier19 code is hosted on GitHub:                    #
# https://github.com/stepan-tsirkin/wannier19                #
#                     written by                             #
#           Stepan Tsirkin, University ofZurich              #
#                                                            #
#------------------------------------------------------------#

import  multiprocessing 
import functools
import numpy as np
from data_dk import Data_dk
from collections import Iterable
import lazy_property
from copy import copy
import symmetry as SYM
from  kpoint import KpointBZ,exclude_equiv_points
import utility



def process(paralfunc,k_list,nproc,symgroup=None,smooth=None):
    selK=[ik for ik,k in enumerate(k_list) if k.res is None]
    dk_list=[k_list[ik].kp_fullBZ for ik in selK]
    print ("processing {0}  points".format(len(dk_list)))
    if nproc<=0:
        res = [paralfunc(k) for k in dk_list]
    else:
        p=multiprocessing.Pool(nproc)
        res= p.map(paralfunc,dk_list)
        p.close()
    if not (symgroup is None):
        res=[symgroup.symmetrize(r) for r in res]
    for i,ik in enumerate(selK):
        k_list[ik].set_res(res[i],smooth)
        



def eval_integral_BZ(func,Data,NKdiv=np.ones(3,dtype=int),nproc=0,NKFFT=None,
            adpt_mesh=2,adpt_num_iter=0,adpt_thresh=None,adpt_nk=1,fout_name="result",fun_write=None,symmetry_gen=[SYM.Identity],smooth=utility.voidsmoother()):
    """This function evaluates in parallel or serial an integral over the Brillouin zone 
of a function func, which whould receive only one argument of type Data_dk, and return 
a numpy.array of whatever dimensions
(TODO: in future it might return whatever object, for which the '+','-',abs and max  operation are defined)

the user has to provide 2 grids of K-points - FFT grid anf NKdiv

The parallelisation is done by NKdiv

As a result, the integration will be performed ove NKFFT x NKdiv
"""
            
    cnt_exclude=0
    NKFFT=Data.NKFFT if NKFFT is None else NKFFT
    
    symgroup=SYM.Group(symmetry_gen,basis=Data.recip_lattice)

    paralfunc=functools.partial(
        _eval_func_k, func=func,Data=Data,NKFFT=NKFFT )

    k_list=KpointBZ(NKFFT=NKFFT,symgroup=symgroup ).divide(NKdiv)
    print ("sum of eights:{}".format(sum(kp.factor for kp in k_list)))


    result_all=[]
    if adpt_num_iter<0:
        adpt_num_iter=-adpt_num_iter*np.prod(NKdiv)/np.prod(adpt_mesh)/adpt_nk/3
    adpt_num_iter=int(round(adpt_num_iter))


    if (adpt_mesh is None) or np.max(adpt_mesh)<=1:
        adpt_num_iter=0
    else:
        if not isinstance(adpt_mesh, Iterable):
            adpt_mesh=[adpt_mesh]*3
        adpt_mesh=np.array(adpt_mesh)
    
    counter=len(k_list)

    for i_iter in range(adpt_num_iter+1):
        print ("iteration {0} - {1} points".format(i_iter,len([k for k in  k_list if k.res is None])) ) #,np.prod(NKFFT)*sum(dk.prod() for dk in dk_list))) 
        process(paralfunc,k_list,nproc,symgroup=symgroup,smooth=smooth)
        result_all.append(sum(kp.get_res for kp in k_list))

        if not (fun_write is None):
            fun_write(result_all[-1],fout_name+"_iter-{0:04d}.dat".format(i_iter))
        
        if i_iter == adpt_num_iter:
            break
             
        # Now add some more points
        select_points=np.sort( list(
                    set(np.argsort([ k.max  for k in k_list])[-adpt_nk:]).union(
                    set(np.argsort([ k.norm for k in k_list])[-adpt_nk:])      ).union(
                    set(np.argsort([ k.normder for k in k_list])[-adpt_nk:])             )
                                 )  )[-1::-1]
        
        cnt1=len(k_list)
        for ik in select_points:
            k_list+=k_list[ik].divide(adpt_mesh)
            del k_list[ik]
        
        print ("sum of eights:{}".format(sum(kp.factor for kp in k_list)))
        print ("checking for equivalent points in all points")
        nexcl=exclude_equiv_points(k_list)
        print (" excluded {0} points".format(nexcl))
        print ("sum of eights now :{}".format(sum(kp.factor for kp in k_list)))
        
        cnt2=len(k_list)
        counter+=cnt2-cnt1
    
    print ("Totally processed {0} k-points ".format(counter))
    return result_all[-1]
       


def _eval_func_k(k,func,Data,NKFFT):
    data_dk=Data_dk(Data,k,NKFFT=NKFFT)
    return func(data_dk)

