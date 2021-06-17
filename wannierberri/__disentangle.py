from .__w90_files import MMN,EIG,AMN,WIN,DMN,CheckPoint
from copy import deepcopy
import numpy as np
from .__system_wannierise import System_Wannierise
from .__utility import fourier_q_to_R
from copy import copy
DEGEN_THRESH=1e-2  # for safity - avoid splitting (almost) degenerate states between free/frozen  inner/outer subspaces  (probably too much)


class CheckPoint_bare(CheckPoint):

    def __init__(self):
        pass





class AbInitioData():
    """A class to describe all input files of wannier90, and to construct the Wannier functions 
     via disentanglement procedure"""
# todo :  rotatre uHu and spn
# todo : create a model from this
# todo : symmetry

    def __init__(self,seedname="wannier90",sitesym=False):
        self.seedname=copy(seedname)
        self.chk=CheckPoint_bare()
        win=WIN(self.seedname)
        self.chk.mp_grid=win.get_param("mp_grid",dtype=int,size=3)
        self.chk.kpt_latt=win.get_param_block("kpoints",dtype=float,shape=(np.prod(self.chk.mp_grid),3))
        self.chk.real_lattice=win.get_param_block("unit_cell_cart",dtype=float,shape=(3,3))
        self.eig=EIG(self.seedname)
        self.mmn=MMN(self.seedname)
        self.amn=AMN(self.seedname)
        assert self.eig.NK==self.amn.NK==self.mmn.NK
        assert self.eig.NB>=self.amn.NB
        assert self.eig.NB>=self.mmn.NB
        self.NK=self.eig.NK
        self.NW=self.amn.NW
        self.NB=self.mmn.NB
        self.chk.recip_lattice=2*np.pi*np.linalg.inv(self.chk.real_lattice).T
        self.mmn.set_bk(mp_grid=self.chk.mp_grid,kpt_latt=self.chk.kpt_latt,recip_lattice=self.chk.recip_lattice)
        self.Mmn=self.mmn.data # [m for m in self.mmn.data]
        self.Amn=self.amn.data # [a for a in self.amn.data]
        self.Eig=self.eig.data # [e for e in self.eig.data]
        self.win_index=[np.arange(self.eig.NB)]*self.NK
        self.disentangled=False
        if sitesym:
            self.Dmn=DMN(self.seedname,num_wann=self.NW)
        else:
            self.Dmn=DMN(None,num_wann=self.NW,num_bands=self.NB,nkpt=self.NK)



    # TODO : allow k-dependent window (can it be useful?)
    def apply_outer_window(self,
                     win_min=-np.Inf,
                     win_max= np.Inf ):
        raise NotImplementedError("outer window does not work so far")
        "Excludes the bands from outside the outer window"

        def win_index_nondegen(ik,thresh=DEGEN_THRESH):
            "define the indices of the selected bands, making sure that degenerate bands were not split"
            E=self.Eig[ik]
            ind=np.where( ( E<=win_max)*(E>=win_min) )[0]
            while ind[0]>0 and E[ind[0]]-E[ind[0]-1]<thresh:
                ind=[ind[0]-1]+ind
            while ind[0]<len(E) and E[ind[-1]+1]-E[ind[-1]]<thresh:
                ind=ind+[ind[-1]+1]
            return ind

        win_index_irr=[win_index_nondegen(ik) for ik in self.Dmn.kptirr]
#        self.excluded_bands=[list(set(ind)
        self.Dmn.select_bands(win_index_irr)
        win_index=[win_index_irr[ik] for ik in self.Dmn.kpt2kptirr]
        self._Eig=[E[ind] for E, ind in zip(self._Eig,win_index)]
        self._Mmn=[[self._Mmn[ik][ib][win_index[ik],:][:,win_index[ikb]] for ib,ikb in enumerate(self.mmn.neighbours[ik])] for ik in range(self.NK)]
        self._Amn=[self._Amn[ik][win_index[ik],:] for ik in range(self.NK)]

    # TODO : allow k-dependent window (can it be useful?)
    def disentangle(self,
                 froz_min=np.Inf,
                 froz_max=-np.Inf,
                 num_iter=100,
                 conv_tol=1e-9,
                 mix_ratio=0.5,
                 num_iter_converge=10,
                 ):

        assert 0<mix_ratio<=1
        def frozen_nondegen(ik,thresh=DEGEN_THRESH):
            """define the indices of the frozen bands, making sure that degenerate bands were not split 
            (unfreeze the degenerate bands together) """
            E=self.eig.data[ik]
            ind=np.where( ( E<=froz_max)*(E>=froz_min) )[0]
            while len(ind)>0 and ind[0]>0 and E[ind[0]]-E[ind[0]-1]<thresh:
                del(ind[0])  
            while len(ind)>0 and ind[0]<len(E) and E[ind[-1]+1]-E[ind[-1]]<thresh:
                del(ind[-1])
            froz=np.zeros(E.shape,dtype=bool)
            froz[ind]=True
            return froz

        frozen_irr=[frozen_nondegen(ik) for ik in self.Dmn.kptirr]
        self.frozen=np.array([ frozen_irr[ik] for ik in self.Dmn.kpt2kptirr ])
        self.free= np.array([ np.logical_not(frozen) for frozen in self.frozen])
        self.Dmn.set_free(frozen_irr)
        self.nBfree=np.array([ np.sum(free) for free in self.free ])
        self.nWfree=np.array([ self.NW-np.sum(frozen) for frozen in self.frozen])
        irr=self.Dmn.kptirr
        U_opt_free_irr=self.get_max_eig(  [ self.Amn[ik][free,:].dot(self.Amn[ik][free,:].T.conj()) 
                        for ik,free in zip(irr,self.free[irr])]  ,self.nWfree[irr],self.nBfree[irr]) # nBfee x nWfree marrices
        # initial guess : eq 27 of SMV2001
        U_opt_free=self.symmetrize_U_opt(U_opt_free_irr,free=True)

        Mmn_FF=self.Mmn_Free_Frozen(self.Mmn,self.free,self.frozen,self.mmn.neighbours,self.mmn.wk,self.NW)

        def calc_Z(Mmn_loc,U=None):
        # TODO : symmetrize (if needed) 
            if U is None: 
               Mmn_loc_opt=[Mmn_loc[ik] for ik in self.Dmn.kptirr]
            else:
               mmnff=Mmn_FF('free','free')
               mmnff=[mmnff[ik] for ik in self.Dmn.kptirr]
               Mmn_loc_opt=[[Mmn[ib].dot(U[ikb]) for ib,ikb in enumerate(neigh)] for Mmn,neigh in zip(mmnff,self.mmn.neighbours[irr])]
            return [sum(wb*mmn.dot(mmn.T.conj()) for wb,mmn in zip(wbk,Mmn)) for wbk,Mmn in zip(self.mmn.wk,Mmn_loc_opt) ]

        Z_frozen=calc_Z(Mmn_FF('free','frozen')) #  only for irreducible

#        print ( '+---------------------------------------------------------------------+<-- DIS\n'+
#                '|  Iter     Omega_I(i-1)      Omega_I(i)      Delta (frac.)    Time   |<-- DIS\n'+
#                '+---------------------------------------------------------------------+<-- DIS'  )

        Omega_I_list=[]
        for i_iter in range(num_iter):
            Z=[(z+zfr)  for z,zfr in zip(calc_Z(Mmn_FF('free','free'),U_opt_free),Z_frozen) ]  # only for irreducible
            if i_iter>0 and mix_ratio<1:
                Z=[ (mix_ratio*z + (1-mix_ratio)*zo) for z,zo in zip(Z,Z_old) ]  #  only for irreducible
            U_opt_free_irr=self.get_max_eig(Z,self.nWfree[irr],self.nBfree[irr]) #  only for irreducible
            U_opt_free=self.symmetrize_U_opt(U_opt_free_irr,free=True)
            Omega_I=sum(Mmn_FF.Omega_I(U_opt_free))
            Omega_I_list.append(Omega_I)
            try:
                _delta=Omega_I-Omega_I_list[-2] 
            except IndexError:
                _delta= "--"
#            print ("iteration {:4d}".format(i_iter)+" Omega_I= "+"  ".join("{:15.10f}".format(x) for x in Omega_I)+" tot =","{:15.10f}".format(sum(Omega_I)))
            print ("iteration {:4d}".format(i_iter)+" Omega_I = {:15.10f}".format(Omega_I)+f"  delta={_delta}")
            if i_iter+1>=num_iter_converge:
                if np.std(Omega_I_list[-num_iter_converge:])<conv_tol:
                    break
            Z_old=deepcopy(Z)

        U_opt_full_irr=[]
#        print (self.Dmn.kptirr
        for ik in self.Dmn.kptirr:
           nband=self.Eig[ik].shape[0]
           U=np.zeros((nband,self.NW),dtype=complex)
           nfrozen=sum(self.frozen[ik])
           nfree=sum(self.free[ik])
           assert nfree+nfrozen==nband
           assert nfrozen<=self.NW, "number of frozen bands {} at k-point {} is greater than number of wannier functions {}".format(nfrozen,ik+1,self.NW)
           U[self.frozen[ik] , range( nfrozen) ] = 1.
           U[self.free[ik]   , nfrozen : ] = U_opt_free[ik]
           Z,D,V=np.linalg.svd(U.T.conj().dot(self.Amn[ik]))
           U_opt_full_irr.append(U.dot(Z.dot(V)))
        U_opt_full=self.symmetrize_U_opt(U_opt_full_irr,free=False)
        self.chk.v_matrix=U_opt_full
        self.disentangled=True


       # now rotating to the optimized space
#        self.Hmn=[]
#        print (self.Amn.shape)
#        for ik in range(self.NK):
#            U=U_opt_full[ik]
#            Ud=U.T.conj()
            # hamiltonian is not diagonal anymore
#            self.Hmn.append(Ud.dot(np.diag(self.Eig[ik])).dot(U))
#            self.Amn[ik]=Ud.dot(self.Amn[ik])
#            self.Mmn[ik]=[Ud.dot(M).dot(U_opt_full[ibk]) for M,ibk in zip (self.Mmn[ik],self.neighbours[ik])]

    def check_disentangled(self,msg):
        if not self.disentangled: 
            raise RuntimeError(f"no disentanglement was performed on the abinitio data, cannot proceed with {msg}")


    def symmetrize_U_opt(self,U_opt_free_irr,free=False):
        # TODO : first symmetrize by the little group
        # Now distribute to reducible points
        d_band=self.Dmn.d_band_free if free else self.Dmn.d_band
        U_opt_free=[d_band[ikirr][isym] @ U_opt_free_irr[ikirr] @ self.Dmn.D_wann_dag[ikirr][isym] for isym,ikirr in zip(self.Dmn.kpt2kptirr_sym,self.Dmn.kpt2kptirr)  ]
        return U_opt_free

           
    def rotate(self,mat,ik1,ik2):
        # data should be of form NBxNBx ...   - any form later
        if len(mat.shape)==1:
            mat=np.diag(mat)
        assert mat.shape[:2]==(self.num_bands,)*2
        shape=mat.shape[2:]
        mat=mat.reshape(mat.shape[:2]+(-1,)).transpose(2,0,1)
        mat=mat[self.win_min[ik1]:self.win_max[ik1],self.win_min[ik2]:self.win_max[ik2]]
        v1=self.v_matrix[ik1].conj()
        v2=self.v_matrix[ik2].T
        return np.array( [v1.dot(m).dot(v2) for m in mat]).transpose( (1,2,0) ).reshape( (self.num_wann,)*2+shape )


    def write_files(self,seedname="wannier90"):
        "Write the disentangled files , where num_wann==num_bands"
        Eig=[]
        Uham=[]
        Amn=[]
        Mmn=[]
        for H in self.Hmn:
            E,U=np.linalg.eigh(H)
            Eig.append(E)
            Uham.append(U)
        EIG(data=Eig).write(seedname)
        for ik in range(self.NK):
            U=Uham[ik]
            Ud=U.T.conj()
            Amn.append(Ud.dot(self.Amn[ik]))
            Mmn.append([Ud.dot(M).dot(Uham[ibk]) for M,ibk in zip (self.Mmn[ik],self.mmn.neighbours[ik])])
        MMN(data=Mmn,G=self.G,bk_cart=self.mmn.bk_cart,wk=self.mmn.wk,neighbours=self.mmn.neighbours).write(seedname)
        AMN(data=Amn).write(seedname)

    def get_max_eig(self,matrix,nvec,nBfree):
        """ return the nvec column-eigenvectors of matrix with maximal eigenvalues. 
        Both matrix and nvec are lists by k-points with arbitrary size of matrices"""
        assert len(matrix)==len(nvec)==len(nBfree)
        assert np.all([m.shape[0]==m.shape[1] for m in matrix])
        assert np.all([m.shape[0]>=nv for m,nv in zip(matrix,nvec)]), "nvec={}, m.shape={}".format(nvec,[m.shape for m in matrix])
        EV=[np.linalg.eigh(M) for M in matrix]
        return [ ev[1][:,np.argsort(ev[0])[nf-nv:nf]] for ev,nv,nf  in zip(EV,nvec,nBfree) ] 

    @property
    def wannier_centres(self):
        WC=np.zeros( (self.NW,3) )
        for ik in range(self.NK):
            for ib,iknb in enumerate(self.mmn.neighbours[ik]) :
                AAW=self.Mmn[ik][ib].diagonal()
                WC -= np.log(AAW).imag[:,None]*self.mmn.wk[ik,ib]*self.mmn.bk_cart[ik,ib,None,:]
        return WC/self.NK
    
    def getSystem(self,**parameters):
        return System_Wannierise(self,**parameters)


    class Mmn_Free_Frozen():
        # TODO : make use of irreducible kpoints (maybe)
        """ a class to store and call the Mmn matrix between/inside the free and frozen subspaces, as well as to calculate the streads"""
        def __init__(self,Mmn,free,frozen,neighbours,wb,NW):
           self.NK=len(Mmn)
           self.wk=wb
           self.neighbours=neighbours
           self.data={}
           self.spaces={'free':free,'frozen':frozen}
           for s1,sp1 in self.spaces.items():
               for s2,sp2 in self.spaces.items():
                   self.data[(s1,s2)]=[[Mmn[ik][ib][sp1[ik],:][:,sp2[ikb]] 
                             for ib,ikb in enumerate(neigh)] for ik,neigh in enumerate(self.neighbours)]
           self.Omega_I_0=NW*self.wk[0].sum()
           self.Omega_I_frozen=-sum( sum( wb*np.sum(abs(mmn[ib])**2) for ib,wb in enumerate(WB)) for WB,mmn in zip(self.wk,self('frozen','frozen')))/self.NK

        def __call__(self,space1,space2):
            assert space1 in self.spaces
            assert space2 in self.spaces
            return self.data[(space1,space2)]

        def Omega_I_free_free(self,U_opt_free):
            U=U_opt_free
            Mmn=self('free','free')
            return -sum( self.wk[ik][ib]*np.sum(abs(   U[ik].T.conj().dot(Mmn[ib]).dot(U[ikb])  )**2) 
                        for ik,Mmn in enumerate(Mmn) for ib,ikb in enumerate(self.neighbours[ik])  )/self.NK

        def Omega_I_free_frozen(self,U_opt_free):
            U=U_opt_free
            Mmn=self('free','frozen')
            return -sum( self.wk[ik][ib]*np.sum(abs(   U[ik].T.conj().dot(Mmn[ib])  )**2) 
                        for ik,Mmn in enumerate(Mmn) for ib,ikb in enumerate(self.neighbours[ik])  )/self.NK*2


        def Omega_I(self,U_opt_free):
            return self.Omega_I_0,self.Omega_I_frozen,self.Omega_I_free_frozen(U_opt_free),self.Omega_I_free_free(U_opt_free)

