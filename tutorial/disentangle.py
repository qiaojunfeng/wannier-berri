import wannierberri as wb
import numpy as np
aidata=wb.AbInitioData(seedname='wannier90')
#aidata.apply_outer_window(win_min=-np.Inf,win_max= 15 )
aidata.disentangle( froz_min=np.Inf,
                 froz_max=9,
                 num_iter=200,
                 conv_tol=1e-9,
                 mix_ratio=0.5
                 )
print (aidata.wannier_centres)
system=aidata.getSystem()
#aidata.write_files(seedname="wannier90-disentangled")
#system=wb.System_Wanneirise(aidata)