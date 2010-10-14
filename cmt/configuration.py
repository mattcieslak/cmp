""" The configuration modules exposes a configuration class based on traits
that is used to create the configuration for a project. Traits attribute are used
to check if the pipeline supports the options """

import enthought.traits.api as traits
import os.path as op, os
import sys
import datetime as dt
from cmt.logme import getLog

class PipelineConfiguration(traits.HasTraits):
       
    # project settings
    project_name = traits.Str(desc="the name of the project")
    project_dir = traits.Directory(exists=True, desc="data path to where the project is stored")
        
    # project metadata (for connectome file)
    project_metadata = traits.Dict(desc="project metadata to be stored in the connectome file")
    generator = traits.Enum( "cmt 1.1", ["cmt 1.1"] )
        
    # subject list
    subject_list = traits.Dict(desc="a dictionary representing information about single subjects")
    
    # choose between 'L' (linear) and 'N' (non-linear)
    registration_mode = traits.Enum("L", ["L", "N"], desc="registration mode: linear or non-linear")
    
    # going to support qBall, HARDI
    processing_mode = traits.Enum( ('DSI', 'Lausanne2011'), [('DSI', 'Lausanne2011'), ('DTI', 'Lausanne2011')], desc="diffusion MRI processing mode available")   
    
    diffusion_imaging_model = traits.Enum( "DSI", ["DSI", "DTI", "HARDI/Q-Ball" ])
    diffusion_imaging_stream = traits.Enum( "Lausanne2011", ["Lausanne2011"] )
    
    nr_of_gradient_directions = traits.Int(515)
    nr_of_sampling_directions = traits.Int(181)
    
    odf_recon_param = traits.Str('-b0 1 -dsi -p 4 -sn 0 -ot nii')
    streamline_param = traits.Str('--angle 60 --rSeed 4')
    
    lin_reg_param = traits.Str('-usesqform -nosearch -dof 6 -cost mutualinfo')
    nlin_reg_bet_T2_param = traits.Str('-f 0.35 -g 0.15')
    nlin_reg_bet_b0_param = traits.Str('-f 0.2 -g 0.2')
    nlin_reg_fnirt_param = traits.Str('')

    # subject
    subject_name = traits.Str(  )
    subject_timepoint = traits.Str( )
    subject_workingdir = traits.Directory
    subject_description = traits.Str( "" )
    subject_raw_glob_diffusion = traits.Str( "*.ima" )
    subject_raw_glob_T1 = traits.Str( "*.ima" )
    subject_raw_glob_T2 = traits.Str( "*.ima" )
        
    active_dicomconverter = traits.Bool(True)
    active_registration = traits.Bool(True)
    active_segmentation = traits.Bool(True)
    active_maskcreation = traits.Bool(True)
    active_reconstruction = traits.Bool(True)
    active_tractography = traits.Bool(True)
    active_fiberfilter = traits.Bool(True)
    active_connectome = traits.Bool(True)
    active_cffconverter = traits.Bool(True)

    author = traits.Str()
    institution = traits.Str()
    creationdate = traits.Str()
    modificationdate = traits.Str()
    species = traits.Str()
    legalnotice = traits.Str()
    reference = traits.Str()
    url = traits.Str()
    description = traits.Str()
                        
    # do you want to do manual whit matter mask correction?
    wm_handling = traits.Enum(1, [1,2,3], desc="in what state should the freesurfer step be processed")
    
    # custom parcellation
    parcellation = traits.Dict(desc="provide the dictionary with your parcellation.")
    
    # start up fslview
    inspect_registration = traits.Bool(False, desc='start fslview to inspect the the registration results')
    fsloutputtype = traits.Enum( 'NIFTI', ['NIFTI'] )
    
    # email notification, needs a local smtp server
    # sudo apt-get install postfix
    emailnotify = traits.ListStr([], desc='the email address to send to')
    
    ################################
    # External package Configuration
    ################################
    
    freesurfer_home = traits.Directory(exists=True, desc="path to Freesurfer")
    fsl_home = traits.Directory(exists=True, desc="path to FSL")
    dtk_home = traits.Directory(exists=True, desc="path to diffusion toolkit")
    dtk_matrices = traits.Directory(exists=True, desc="path to diffusion toolkit matrices")

    def __init__(self, **kwargs):
        # NOTE: In python 2.6, object.__init__ no longer accepts input
        # arguments.  HasTraits does not define an __init__ and
        # therefore these args were being ignored.
        super(PipelineConfiguration, self).__init__(**kwargs)

        # the default parcellation provided
        default_parcell = {'scale33' : {'number_of_regions' : 0,
                                        # contains name, url, color, freesurfer_label, etc. used for connection matrix
                                        'node_information_graphml' : op.join(self.get_lausanne_parcellation_path('resolution85'), 'resolution85.graphml'),
                                        # scalar node values on fsaverage? or atlas? 
                                        'surface_parcellation' : None,
                                        # scalar node values in fsaverage volume?
                                        'volume_parcellation' : None,
                                        # the subdirectory name from where to copy parcellations, with hemispheric wildcard
                                        'fs_label_subdir_name' : 'regenerated_%s_35',
                                        # should we subtract the cortical rois for the white matter mask?
                                        'subtract_from_wm_mask' : 1,
                                        }#,
#                           'scale60' : {'fs_label_subdir_name' : 'regenerated_%s_60'},
#                           'scale125' : {'fs_label_subdir_name' : 'regenerated_%s_125'},
#                           'scale250' : {'fs_label_subdir_name' : 'regenerated_%s_250'},
#                           'scale500' : {'fs_label_subdir_name' : 'regenerated_%s_500'}
                           }
        
        self.parcellation = default_parcell
        
        # no email notify
        self.emailnotify = []
        
        # try to discover paths from environment variables
        try:
            self.freesurfer_home = op.join(os.environ['FREESURFER_HOME'])
            self.fsl_home = op.join(os.environ['FSL_HOME'])
            self.dtk_home = os.environ['DTDIR']
            self.dtk_matrices = op.join(myp.dtk_home, 'matrices')
        except KeyError:
            pass
        
        self.fsloutputtype = 'NIFTI'
        os.environ['FSLOUTPUTTYPE'] = self.fsloutputtype
        os.environ['FSLOUTPUTTYPE'] = 'NIFTI'
                

    def consistency_check(self):
        """ Provides a checking facility for configuration objects """
        
        # project name not empty
        if self.project_name == '' or self.project_name == None:
            msg = 'You have to set a project name!'
            raise Exception(msg)
        
        # check if software paths exists
        pas = {'configuration.freesurfer_home' : self.freesurfer_home,
               'configuration.fsl_home' : self.fsl_home,
               'configuration.dtk_home' : self.dtk_home,
               'configuration.dtk_matrices' : self.dtk_matrices}
        for k,p in pas.items():
            if not op.exists(p):
                msg = 'Required software path for %s does not exists: %s' % (k, p)
                raise Exception(msg)
                
        if self.processing_mode[0] == 'DSI':
            ke = self.mode_parameters.keys()

            if not 'nr_of_gradient_directions' in ke:
                raise Exception('Parameter "nr_of_gradient_directions" not set as key in mode_parameters. Required for DSI.')
                
            if not 'nr_of_sampling_directions' in ke:
                raise Exception('Parameter "nr_of_sampling_directions" not set as key in mode_parameters. Required for DSI.')

        for subj in self.subject_list:
            
            if not self.subject_list[subj].has_key('workingdir'):
                msg = 'No working directory defined for subject %s' % str(subj)
                raise Exception(msg)
            else:
                wdir = self.get_subj_dir(subj)
                if not op.exists(wdir):
                    msg = 'Working directory %s does not exists for subject %s' % (wdir, str(subj))
                    raise Exception(msg)
                else:
                    wdiff = op.join(self.get_raw_diffusion4subject(subj))
                    print wdiff
                    if not op.exists(wdiff):
                        msg = 'Diffusion MRI subdirectory %s does not exists for subject %s' % (wdiff, str(subj))
                        raise Exception(msg)
                    wt1 = op.join(self.get_rawt14subject(subj))
                    if not op.exists(wt1):
                        msg = 'Stuctural MRI subdirectory %s does not exists for subject %s' % (wt1, str(subj))
                        raise Exception(msg)
        
        
    def get_cmt_home(self):
        """ Return the cmt home path """
        return op.dirname(__file__)
        
    def get_raw4subject(self, subject):
        """ Return raw data path for subject """
        return op.join(self.get_subj_dir(subject), '1__RAWDATA')
    
    def get_log4subject(self, subject):
        """ Get subject log dir """
        return op.join(self.get_subj_dir(subject), '0__LOG')
    
    def get_rawglob(self, modality, subject):
        """ Get the file name endings for modality and subject """
        
        if modality == 'diffusion':
            if self.subject_list[subject].has_key('raw_glob_diffusion'):
                return self.subject_list[subject]['raw_glob_diffusion']
            else:
                raise Exception('No raw_glob_diffusion defined for subject %s' % subject)

        elif modality == 'T1':
            if self.subject_list[subject].has_key('raw_glob_T1'):
                return self.subject_list[subject]['raw_glob_T1']
            else:
                raise Exception('No raw_glob_T1 defined for subject %s' % subject)
            
        elif modality == 'T2':
            if self.subject_list[subject].has_key('raw_glob_T2'):
                return self.subject_list[subject]['raw_glob_T2']
            else:
                raise Exception('No raw_glob_T2 defined for subject %s' % subject)
        
    
    def get_logger4subject(self, subject):
        """ Get the logger instance created """
        if not self.subject_list[subject].has_key('logger'):
            # setup logger for the subject
            self.subject_list[subject]['logger'] = \
                getLog(os.path.join(self.get_log4subject(subject), \
                        'pipeline-%s-%s-%s.log' % (str(dt.datetime.now()), subject[0], subject[1] ) )) 
            return self.subject_list[subject]['logger'] 
        else: 
            return self.subject_list[subject]['logger']
    
    def get_rawt14subject(self, subject):
        """ Get raw structural MRI T1 path for subject """
        return op.join(self.get_subj_dir(subject), '1__RAWDATA', 'T1')

    def get_rawt24subject(self, subject):
        """ Get raw structural MRI T2 path for subject """
        return op.join(self.get_subj_dir(subject), '1__RAWDATA', 'T2')

    def get_raw_diffusion4subject(self, subject):
        """ Get the raw diffusion path for subject """
        if self.processing_mode[0] == 'DSI':
            return op.join(self.get_subj_dir(subject), '1__RAWDATA', 'DSI')
        elif self.processing_mode[0] == 'DTI':
            return op.join(self.get_subj_dir(subject), '1__RAWDATA', 'DTI')
        
    def get_fs4subject(self, subject):
        """ Returns the subject root folder path for freesurfer files """
        return op.join(self.get_subj_dir(subject), '3__FREESURFER')
        
    def get_nifti4subject(self, subject):
        """ Returns the subject root folder path for nifti files """
        return op.join(self.get_subj_dir(subject), '2__NIFTI')

    def get_cmt4subject(self, subject):
        return op.join(self.get_subj_dir(subject), '4__CMT')

    def get_cmt_rawdiff4subject(self, subject):
        return op.join(self.get_subj_dir(subject), '4__CMT', 'raw_diffusion')
        
    def get_cmt_fsout4subject(self, subject):
        return op.join(self.get_subj_dir(subject), '4__CMT', 'fs_output')
    
    def get_cmt_fibers4subject(self, subject):
        return op.join(self.get_subj_dir(subject), '4__CMT', 'fibers')

    def get_cmt_scalars4subject(self, subject):
        return op.join(self.get_subj_dir(subject), '4__CMT', 'scalars')

    def get_matMask4subject(self, subject):
        if not self.mode_parameters.has_key('mat_mask'):
            return op.join(op.dirname(__file__), 'data', 'parcellation', 'lausanne2008', 'resolution83', 'mat_mask.npy')
        else:
            return self.mode_parameters['mat_mask']
        
    def get_cmt_matrices4subject(self, subject):
        return op.join(self.get_subj_dir(subject), '4__CMT', 'fibers', 'matrices')    

    def get_cmt_tracto_mask(self, subject):
        return op.join(self.get_cmt_fsout4subject(subject), 'registred', 'HR')
    
    def get_cmt_tracto_mask_tob0(self, subject):
        return op.join(self.get_cmt_fsout4subject(subject), 'registred', 'HR__registered-TO-b0')

    def get_subj_dir(self, subject):
        return self.subject_list[subject]['workingdir']

    def get_gradient_matrix(self, subject, raw = True):
        """ Returns the absolute path to the gradient matrix
        (the b-vectors) extracted from the raw diffusion DICOM files """
        
        if self.processing_mode[0] == 'DSI':
            return op.join(self.get_nifti4subject(subject), 'dsi_bvects.txt')
        elif  self.processing_mode[0] == 'DTI':
            if raw:
                # return the raw table
                return op.join(self.get_nifti4subject(subject), 'dti_bvects.txt')
            else:
                # return the processed table with nan set to 0 and 4th component are the bvals
                
                pass

    def get_cmt_scalarfields(self, subject):
        """ Returns a list with tuples with the scalar field name and the
        absolute path to its nifti file """
        
        ret = []
        
        if self.processing_mode[0] == 'DSI':
            # add gfa per default
            ret.append( ('gfa', op.join(self.get_cmt_scalars4subject(subject), 'dsi_gfa.nii')))
            # XXX: add adc per default
            
        elif  self.processing_mode[0] == 'DTI':
            # nothing to add yet for DTI
            pass
        
        return ret
        
        
    def get_dtk_dsi_matrix(self):
        """ Returns the DSI matrix from Diffusion Toolkit
        
        The mode_parameters have to be set in the configuration object with keys:
        1. number of gradient directions : 'nr_of_gradient_directions'
        2. number of sampling directions : 'nr_of_sampling_directions'
        
        Example
        -------
        
        confobj.mode_parameters['nr_of_gradient_directions'] = 515
        confobj.mode_parameters['nr_of_sampling_directions'] = 181
        
        Returns matrix including absolute path to DSI_matrix_515x181.dat
        
        """
        
        # XXX: check fist if it is available at all
        if not self.mode_parameters.has_key('nr_of_gradient_directions'):
            msg = 'nr_of_gradient_directions not set in mode_parameters'
            raise Exception(msg)
        if not self.mode_parameters.has_key('nr_of_sampling_directions'):
            msg = 'nr_of_sampling_directions not set in mode_parameters'
            raise Exception(msg)
         
        grad = self.mode_parameters['nr_of_gradient_directions']
        samp = self.mode_parameters['nr_of_sampling_directions']
        fpath = op.join(self.dtk_matrices, "DSI_matrix_%sx%s.dat" % (grad, samp))
        if not op.exists(fpath):
            msg = "DSI matrix does not exists: %s" % fpath
            raise Exception(msg)
            
        return fpath
    
    
    def get_lausanne_atlas(self, name = None):
        """ Return the absolute path to the lausanne parcellation atlas
        for the resolution name """
        
        cmt_path = op.dirname(__file__)
        
        provided_atlases = ['myatlas_33_rh.gcs','myatlasP1_16_rh.gcs','myatlasP17_28_rh.gcs','myatlasP29_35_rh.gcs',
                            'myatlas_60_rh.gcs','myatlas_125_rh.gcs','myatlas_250_rh.gcs','myatlas_33_lh.gcs','myatlasP1_16_lh.gcs',
                            'myatlasP17_28_lh.gcs','myatlasP29_35_lh.gcs','myatlas_60_lh.gcs','myatlas_125_lh.gcs','myatlas_250_lh.gcs']
        
        if name in provided_atlases:
            return op.join(cmt_path, 'data', 'colortable_and_gcs', 'my_atlas_gcs', name)
    
        
    def get_lausanne_parcellation_path(self, parcellationname):
        
        cmt_path = op.dirname(__file__)
        
        allowed_default_parcel = ['resolution85', 'resolution150', 'resolution258', 'resolution500', 'resolution1015']
        
        if parcellationname in allowed_default_parcel:
            return op.join(cmt_path, 'data', 'parcellation', 'lausanne2008', parcellationname)
        else:
            log.error("Not a valid default parcellation name for the lausanne2008 parcellation scheme")
        
        
    def get_cmt_binary_path(self):
        """ Returns the path to the binary files for the current platform
        and architecture """
        
        if sys.platform == 'linux2':
    
            import platform as pf
            if '32' in pf.architecture()[0]:
                return op.join(op.dirname(__file__), "binary", "linux2", "bit32")
            elif '64' in pf.architecture()[0]:
                return op.join(op.dirname(__file__), "binary", "linux2", "bit64")
        else:
            raise('No binary files compiled for your platform!')
    
