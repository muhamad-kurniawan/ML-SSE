import pandas as pd
from utilities import count_element_ratio as cer
import numpy as np


cations = [
    "Li", "Be", "Na", "Mg", "Al", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", 
    "Co", "Ni", "Cu", "Zn", "Ga", "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", 
    "Pd", "Ag", "Cd", "In", "Sn", "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", 
    "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", 
    "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", 
    "Cf", "Es", "Fm", "Md", "No", "Lr", "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", 
    "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og", "Si", "Ge", "As", "Sb", "Te", "At", "P","B",
]

anions = [
    "H",  "C", "N", "O", "F", "S", "Cl", "Se", "Br", "I", "Te", "At", "Ts", "Po",
]

possible_dual_type = ['P']

schemes=['avg','dev', 'max','min','range']

def apply_scheme(molecules_, target_, schemes=schemes, descriptor='data/element_properties/features.csv', lambda_transform=-2):
    molecules = list(molecules_)
    target = list(target_)
    elements_feature = pd.read_csv(descriptor)
    ratios = cer.list_element_stoichiometri(molecules)
    features = elements_feature.copy()
    df_final = pd.DataFrame()
    molecules_ = []
    target_ = []

    ori_feature_columns = list(features.columns)[1:]
    for n_mol in range(len(ratios)):
        ratio = ratios[n_mol]
        element_cation = []
        element_anion = []
        exotic_elements = False
        anion_not_found = False

        for el in ratio[0]:            
            if el not in list(elements_feature.iloc[:,0]):
                exotic_elements = True
        if exotic_elements == True:
            continue
        
        for n_elem in range(len(ratio[0])):
            if ratio[0][n_elem] in cations:
                element_cation.append([ratio[0][n_elem], ratio[1][n_elem]])
            elif ratio[0][n_elem] in anions:
                element_anion.append([ratio[0][n_elem], ratio[1][n_elem]])

        #check if no anion list is found on formula. if not found, check possible_dual_type
        if len(element_anion)==0:
            possible_anion = [el for el in ratio[0] if el in possible_dual_type]
            if len(possible_anion) > 0: #assumed only 1 element in the cation list is an anion, if there are more than 1 element, only the first element is considered
                #recalculate with updated cation and anion list
                element_cation = []
                element_anion = []
                cations_ = cations.copy()
                anions_ = anions.copy()
                cations_.remove(possible_anion[0])
                anions_.append(possible_anion[0])
                for n_elem in range(len(ratio[0])):
                    if ratio[0][n_elem] in cations_:
                        element_cation.append([ratio[0][n_elem], ratio[1][n_elem]])
                    elif ratio[0][n_elem] in anions_:
                        element_anion.append([ratio[0][n_elem], ratio[1][n_elem]])
            else:
                print('anion not found in {}, ratio anion will assumed to be 1/3 to cation'.format(molecules[n_mol]))
                anion_not_found = True


        list_schemes = []
        list_other_features = []
        all_feature_values = []
        list_other_feature_values = []
        total_ratio = sum(ratio[1])

        ratio_cation = sum([elc[1] for elc in element_cation])
        if anion_not_found:
            ratio_anion = ratio_cation/3
        else:
            ratio_anion = sum([elc[1] for elc in element_anion])
        li_ratio = sum([elc[1] if elc[0]=='Li' else 0 for elc in element_cation])
        sum_ratio = ratio_cation+ratio_anion
        if 'ratio_cation' in schemes:
            list_other_feature_values.append(ratio_cation/sum_ratio)
            list_other_features.append('ratio_cation')
        if 'ratio_anion' in schemes:
            list_other_feature_values.append(ratio_anion/sum_ratio)
            list_other_features.append('ratio_anion')
        if 'ratio_cation_to_anion' in schemes:
            list_other_feature_values.append(ratio_cation/ratio_anion)
            list_other_features.append('ratio_cation_to_anion')
        if 'number_cation' in schemes:
            list_other_feature_values.append(len(element_cation))
            list_other_features.append('number_cation')
        if 'number_anion' in schemes:
            if anion_not_found:
                list_other_feature_values.append(1)
            else:
                list_other_feature_values.append(len(element_anion))
            list_other_features.append('number_anion')
        if 'ratio_li_cation' in schemes:
            list_other_feature_values.append(li_ratio/ratio_cation)
            list_other_features.append('ratio_li_cation')
        if 'ratio_li_anion' in schemes:
            list_other_feature_values.append(li_ratio/ratio_anion)
            list_other_features.append('ratio_li_anion')

        avg = sum([get_features(ratio[0][n], features).dot((ratio[1][n]/total_ratio)) for n in range(len(ratio[0]))])
        
        if 'avg' in schemes:
            all_feature_values = all_feature_values + list(avg)
            list_schemes.append('avg')
            # all_feature_values = list(avg)
        if 'dev' in schemes:
            dev_ = sum([abs(get_features(ratio[0][n], features)-avg).dot((ratio[1][n]/total_ratio)) for n in range(len(ratio[0]))])
            all_feature_values = all_feature_values + list(dev_)
            list_schemes.append('dev')
        if 'avg_transformed' in schemes:
            x_max = max(ratio[1])
            scaled_ratio = [x+0.4*(x_max-x) for x in ratio[1]]
            total = sum(scaled_ratio)
            avg_scaled_ratio = sum([get_features(ratio[0][n], features).dot((scaled_ratio[n]/total)) for n in range(len(ratio[0]))])
            all_feature_values = all_feature_values + list(avg_scaled_ratio)
            list_schemes.append('avg_transformed')

        if 'avg_yj' in schemes or 'dev_yj' in schemes:
            yj_ratio = [(((x+1)**lambda_transform)-1)/lambda_transform for x in ratio[1]]
            total_yj_ratio = sum(yj_ratio)
            avg_yj = sum([get_features(ratio[0][n], features).dot((yj_ratio[n]/total_yj_ratio)) for n in range(len(ratio[0]))])
            list_dev_yj = [abs(get_features(ratio[0][n], features)-avg_yj) for n in range(len(ratio[0]))]
            if 'avg_yj' in schemes:
                all_feature_values = all_feature_values + list(avg_yj)
                list_schemes.append('avg_yj')
            if 'dev_yj' in schemes:
                dev_ = sum([list_dev_yj[n].dot((yj_ratio[n]/total_yj_ratio)) for n in range(len(list_dev_yj))])
                all_feature_values = all_feature_values + list(dev_)
                list_schemes.append('dev_yj')

        if 'avg_power' in schemes or 'dev_power' in schemes:
            power_ratio = [x**lambda_transform for x in ratio[1]]
            total_power_ratio = sum(power_ratio)
            avg_power = sum([get_features(ratio[0][n], features).dot((power_ratio[n]/total_power_ratio)) for n in range(len(ratio[0]))])
            list_dev_power = [abs(get_features(ratio[0][n], features)-avg_power) for n in range(len(ratio[0]))]
            if 'avg_power' in schemes:
                all_feature_values = all_feature_values + list(avg_power)
                list_schemes.append('avg_power')
            if 'dev_power' in schemes:
                dev_ = sum([list_dev_power[n].dot((power_ratio[n]/total_power_ratio)) for n in range(len(list_dev_power))])
                all_feature_values = all_feature_values + list(dev_)
                list_schemes.append('dev_power')

        list_element_value = np.array([get_features(ratio[0][n], features) for n in range(len(ratio[0]))]).T
        max_ = [max(n) for n in list_element_value]
        min_ = [min(n) for n in list_element_value]
        if 'max' in schemes:            
            all_feature_values = all_feature_values + list(max_)
            list_schemes.append('max')
        if 'min' in schemes:
            all_feature_values = all_feature_values + list(min_)
            list_schemes.append('min')
        if 'range' in schemes:
            range_ = np.array(max_)-np.array(min_)
            list_schemes.append('range')
            all_feature_values = all_feature_values + list(range_)
        if 'mode' in schemes:
            list_element_ratio = [ratio[1][n] for n in range(len(ratio[0]))]
            index_ratio_mode = list_element_ratio.index(max(list_element_ratio))
            mode_ = [v.tolist()[index_ratio_mode] for v in list_element_value]
            all_feature_values = all_feature_values + list(mode_)
            list_schemes.append('mode')
        # print(list_schemes)
        
        anion_not_found = False
            
        final_feature_columns = list(np.array([add_prefix(ori_feature_columns, pref) for pref in list_schemes]).reshape(-1))
        if len(list_other_features)>0:
            final_feature_columns.extend(list_other_features)
            all_feature_values.extend(list_other_feature_values)
        df_feat_mol = pd.DataFrame([all_feature_values], columns=final_feature_columns)
        df_final = pd.concat([df_final, df_feat_mol])
        molecules_.append(molecules[n_mol])
        target_.append(target[n_mol])
        
    # print(df_final.shape)
    return df_final.reset_index(drop=True), target_, molecules_, 
        
def get_features(elem, df_features):
    return np.array(df_features[df_features.iloc[:,0]==elem].iloc[:,1:]).reshape(-1)

def add_prefix(all_features_str, prefix):
    return [str(prefix)+'_'+x for x in all_features_str]