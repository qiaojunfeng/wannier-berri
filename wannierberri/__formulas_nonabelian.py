import numpy as np
from .__utility import  alpha_A,beta_A
from .__formula import Formula
from functools import partial
#####################################################
#####################################################

# Here we write some functions, that take a argument Data_K object, op and ed, and return a Formula

def Identity(data_K,op,ed):
        "an identity operator (to compute DOS)"
        # first give our matrices short names
        NB= data_K.nbands
        # This is the formula to be implemented:
        formula =  Formula ( TRodd=False,Iodd=False,ndim=0,name='Identity',nonabelian=True )
        mat = np.zeros((ed-op,NB,NB),dtype=complex)
        for i in range(NB): 
           mat[:,i,i]=1.
        formula.add_term ('mn', mat) 
        return formula


def Velocity(data_K,op,ed):
        "inverse effective mass"
        # first give our matrices short names
        V   = data_K.V_H[op:ed]
        # This is the formula to be implemented:
        formula =  Formula ( TRodd=True,Iodd=True,ndim=1,name="vbelocity",nonabelian=True  )
        formula.add_term ( 'mn'   ,  V ,  1. )
        return formula



def InverseMass(data_K,op,ed):
        "inverse effective mass"
        # first give our matrices short names
        d2E = data_K.del2E_H[op:ed]
        D   = data_K.D_H[op:ed]
        V   = data_K.V_H[op:ed]
        # This is the formula to be implemented:
        formula =  Formula ( TRodd=False,Iodd=False,ndim=2,name="Inverse Mass",nonabelian=True  )
        formula.add_term ( 'mn'   ,  d2E                           ,  1. )
        formula.add_term ( 'mL,Ln',(V[:,:,:,:,None], D[:,:,:,None,:] ) ,  1. )
        formula.add_term ( 'mL,Ln',(D[:,:,:,None,:], V[:,:,:,:,None] ) , -1. )
        return formula


def Der3E(data_K,op,ed):
        "Third derivative of band energy - not completed"
        raise NotImplementedError()
        # first give our matrices short names
        d2E = data_K.del2E_H[op:ed]
        d3E = data_K.del3E_H[op:ed]
        D   = data_K.D_H[op:ed]
        V   = data_K.V_H[op:ed]
        # This is the formula to be implemented:
        formula =  Formula ( TRodd=False,Iodd=False,ndim=2,name="Inverse Mass" )
        formula.add_term ( 'mn'   ,  d2E                           ,  1. )
        formula.add_term ( 'mL,Ln',(V[:,:,:,:,None], D[:,:,:,None,:] ) ,  1. )
        formula.add_term ( 'mL,Ln',(D[:,:,:,None,:], V[:,:,:,:,None] ) , -1. )
        return formula



def Omega(data_K,op=None,ed=None,onlytrace=False):
        "an attempt for a faster implementation"
        # first give our matrices short names
        NB= data_K.nbands
        A = data_K.A_Hbar[op:ed]
        D = data_K.D_H[op:ed]
        O = data_K.Omega_Hbar[op:ed]
        # now define the "alpha" and "beta" components
        A_,D_={},{}
        for var in 'A','D':
            for c in 'alpha','beta':
                locals()[var+"_"][c]=locals()[var][:,:,:,globals()[c+'_A']]
        # This is the formula to be implemented:
        formula =  Formula ( ndim=1,TRodd=True,Iodd=False, name="Berry Curvature")
        formula.add_term( 'mn', (O, ) )
        formula.add_term( 'mL,Ln',(D_['alpha'], D_['beta' ] ) ,-2j )
        if onlytrace:
            formula.add_term( 'mL,Ln',(D_['alpha'], A_['beta' ] ) , -4 )
        else:
            formula.add_term( 'mL,Ln',(D_['alpha'], A_['beta' ] ) , -2 )
            formula.add_term( 'mL,Ln',(D_['beta' ], A_['alpha'] ) ,  2 )
        return formula

Omega_onlytrace=partial(Omega,onlytrace=True)

def Hplusminus(data_K,op=None,ed=None,sign=1):
        "an attempt for a faster implementation"
        assert sign in (1,-1) , "sign should be +1 or -1"
        # first give our matrices short names
        E = data_K.E_K[op:ed]
        A = data_K.A_Hbar[op:ed]
        B = data_K.B_Hbar[op:ed]
        D = data_K.D_H[op:ed]
        M = data_K.Morb_Hbar[op:ed]
        O = data_K.Omega_Hbar[op:ed]
        # now define the "alpha" and "beta" components
        A_,B_,D_={},{},{}
        for var in 'A','B','D':
            for c in 'alpha','beta':
                locals()[var+"_"][c]=locals()[var][:,:,:,globals()[c+'_A']]
        # This is the formula to be implemented:
        formula =  Formula (ndim=1,TRodd=True,Iodd=False,name="Hplusminus")
        formula.add_term( 'mn',(M+sign*O*E[:,:,None,None]))
        if sign == 1:
            formula.add_term( 'ml,ln',(A_['alpha'],E[:,None,:,None]*A_['beta']),2j )
        formula.add_term( 'mL,Ln',(D_['alpha'],B_['beta' ] ),-2 )
        formula.add_term( 'mL,Ln',(D_['beta'],B_['alpha' ] ),2 )
        formula.add_term( 'mL,Ln',(D_['alpha'],E[:,None,:,None]*A_['beta'] ),-2*sign )
        formula.add_term( 'mL,Ln',(D_['beta'],E[:,None,:,None] *A_['alpha'] ),2*sign )
        
        formula.add_term( 'mL,Ln',(D_['alpha'],E[:,:,None,None]*D_['beta'] ),-2j )
        formula.add_term( 'mL,Ln',(D_['alpha'],E[:,None,:,None]*D_['beta'] ),-2j*sign )
        return formula

def derHplus(data_K,op=None,ed=None):
        "an attempt for a faster implementation"
        # first give our matrices short names
        E = data_K.E_K[op:ed]
        W  = data_K.del2E_H[op:ed]
        _V = data_K.V_H[op:ed]
        _D = data_K.D_H[op:ed]
        dOn = data_K.Omega_bar_der.real[op:ed]
        dHn = data_K.Morb_Hbar_der.real[op:ed]
        Bplus = data_K.B_Hbarplus_dagger_fz[op:ed].transpose(0,2,1,3)
        dBpln = data_K.gdBbarplus_fz(op,ed,index='ln')[op:ed]
        B = data_K.B_Hbar_fz[op:ed,:,:,:,None]
        A  = data_K.A_Hbar[op:ed,:,:,:,None]
        f,df=data_K.f_E(1)
        f_m,df_m=data_K.f_E(-1)
        f,df,f_m,df_m=f[op:ed,:,None,None,None],df[op:ed,:,None,None,None],f_m[op:ed,:,None,None,None],df_m[op:ed,:,None,None,None]
        O = data_K.Omega_Hbar[op:ed,:,:,:,None]
        H = data_K.Morb_Hbar[op:ed,:,:,:,None]
        El = E[:,:,None,None]
        En2 = E[:,None,:,None,None]
        El2 = E[:,:,None,None,None]
        En = E[:,None,:,None]
        Bpcal= ((-Bplus-1j*_D*(En+El))*data_K.dEig_inv[op:ed,:,:,None])[:,:,:,:,None]
        
        Bp  =  Bplus[:,:,:,:,None]
        V = _V[:,:,:,:,None]
        Vd = _V[:,:,:,None,:]
        D = _D[:,:,:,:,None]
        Dd = _D[:,:,:,None,:]

        del _V,E,Bplus,_D
        # now define the "alpha" and "beta" components
        Bp_,D_,W_,V_,Bpcal_,dBpln_,B_,A_={},{},{},{},{},{},{},{}
        for var in 'Bp','D','Bpcal','W','V','dBpln','B','A':
            for c in 'alpha','beta':
                locals()[var+"_"][c]=locals()[var][:,:,:,globals()[c+'_A']]
        # This is the formula to be implemented:
        formula =  Formula (ndim=2,TRodd=True,Iodd=False,name="derivative of Hplus" )
        formula.add_term('mn',(dHn+dOn*El2) )
        formula.add_term( 'ml,ln', (O,Vd) )
        formula.add_term( 'nL,Ln', (Dd, O*En2 ),-2)
        formula.add_term( 'nL,Ln', (Dd,H ),-1)
        formula.add_term( 'nL,Ln', (H ,Dd ))
        for s,a,b in ( +1.,'alpha','beta'),(-1.,'beta','alpha'):
            #  blue terms
            formula.add_term( 'mL,Ln',   ( Bpcal_ [a] , W_[b]  ), 2*s )
            formula.add_term( 'mL,LP,Pn',( Bpcal_ [a] , V_[b] , Dd    ),2*s )
            formula.add_term( 'mL,LP,Pn',( Bpcal_ [a] , Vd    , D_[b] ),2*s )
            formula.add_term( 'mL,Ll,ln',( Bpcal_ [a] , D_[b] , Vd    ),-2*s )
            formula.add_term( 'mL,Ll,ln',( Bpcal_ [a] , Dd    , V_[b] ),-2*s )
            #  green terms               
            #  frozen window o B matrix  f
            formula.add_term( 'mL,Ln',   ( D_ [a] , dBpln_[b] ) ,-2*s )
            formula.add_term( 'mL,LP,Pn',( D_ [a] , A_[b]       , Dd*En2 ),-2*s )
            formula.add_term( 'mL,LP,Pn',( D_ [a] , A_[b]*El2*f , Dd     ),-2*s )
            formula.add_term( 'mL,LP,Pn',( D_ [a] , B_[b]*f_m   , Dd     ),-2*s )
            formula.add_term( 'mL,LP,Pn',( D_ [a] , Vd*f        , A_[b]  ),-2*s )
            formula.add_term( 'mL,LP,Pn',( D_ [a] , Vd*df_m*En2 , A_[b]  ),-2*s )
            formula.add_term( 'mL,LP,Pn',( D_ [a] , Vd*df_m     , B_[b]  ),2*s )
            formula.add_term( 'mL,Ll,ln',( D_ [a] , Dd       , A_[b]*En2 ),2*s )
            formula.add_term( 'mL,Ll,ln',( D_ [a] , Dd*El2*f , A_[b]     ),2*s )
            formula.add_term( 'mL,Ll,ln',( D_ [a] , Dd*f_m   , B_[b]     ),2*s )
            formula.add_term( 'mL,Ll,ln',( D_ [a] , A_[b]    , Vd        ),-2*s )
                              
            formula.add_term( 'mL,LP,Pn',(D_[a] , Vd   , D_[b] ),-1j*s)
            formula.add_term( 'mL,Ll,ln',(D_[a] , D_[b] , Vd   ),-1j*s)
        return formula



def derOmega(data_K,op=None,ed=None):
        "an attempt for a faster implementation"
        # first give our matrices short name
#        print ("using kpoint [{}:{}]".format(op,ed))
        A  = data_K.A_Hbar[op:ed]
        dA = data_K.A_Hbar_der[op:ed]
#        print ("dA=",dA)
        _D = data_K.D_H[op:ed]
        _V = data_K.V_H[op:ed]
        O  = data_K.Omega_Hbar[op:ed,:,:,:,None]
        dO = data_K.Omega_bar_der[op:ed]
        W  = data_K.del2E_H[op:ed]

        Acal= (-(A+1j*_D)*data_K.dEig_inv[op:ed,:,:,None])[:,:,:,:,None]
        A  =  A[:,:,:,:,None]
        D  = _D[:,:,:,:,None]
        Dd = _D[:,:,:,None,:]
        V  = _V[:,:,:,:,None]
        Vd = _V[:,:,:,None,:]

        del _D,_V

        # now define the "alpha" and "beta" components
        A_,D_,W_,V_,Acal_,dA_={},{},{},{},{},{}
        for var in 'A','D','Acal','W','V','dA':
            for c in 'alpha','beta':
#                print (var,c,locals()[var].shape)
                locals()[var+"_"][c]=locals()[var][:,:,:,globals()[c+'_A']]
        # This is the formula to be implemented:
        # orange terms
        formula =  Formula( ndim=2,TRodd=False,Iodd=True, name="derivative of berry curvatrue")
        formula.add_term  ('mn',(dO, ) )
        formula.add_term  ( 'mL,Ln',(Dd, O ), -2. )
        for s,a,b in ( +1.,'alpha','beta'),(-1.,'beta','alpha'):
        #    #  blue terms
            formula.add_term( 'mL,Ln',    (Acal_ [a] , W_[b]         ),  2*s )
            formula.add_term( 'mL,LP,Pn', (Acal_ [a] , V_[b] , Dd    ),  2*s )
            formula.add_term( 'mL,LP,Pn', (Acal_ [a] , Vd    , D_[b] ),  2*s )
            formula.add_term( 'mL,Ll,ln', (Acal_ [a] , D_[b] , Vd    ), -2*s )
            formula.add_term( 'mL,Ll,ln', (Acal_ [a] , Dd    , V_[b] ), -2*s )
            #  green terms
            formula.add_term( 'mL,Ln',     (  D_ [a] , dA_[b]        ) , -2*s)
            formula.add_term( 'mL,LP,Pn',  (  D_ [a] , A_[b] , Dd    ) , -2*s)
            formula.add_term( 'mL,Ll,ln',  (  D_ [a] , Dd    , A_[b] ) ,  2*s)
        return formula


