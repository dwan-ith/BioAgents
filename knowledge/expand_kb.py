"""Generate expanded molecules.metta knowledge base."""
import os

# Original molecules to keep
orig = [
    "Cu_ZnO_Al2O3","Pd_SiO2","Rh_Ti","HZSM_5","SAPO_34","Nickel_Alloy",
    "Cellulase_A","Xylanase_B","Laccase_C","Amylase_D",
    "Sulfur_Compound","Coke_Deposit","Heavy_Metal_Ion","Thermal_Stress"
]

# New molecules: (name, mw, formula, cat_tags, targets, func_groups, activity, selectivity, stability_h)
new_mols = [
    # === CHEMICAL CATALYSTS ===
    ("Pt_Al2O3", 195.1, "Pt_on_Al2O3", "chemical_catalyst hydrogenation precious_metal",
     "Naphtha_Reforming Dehydrogenation", "supported_metal alumina_support noble_metal", 0.91, 0.89, 600),
    ("Ru_Carbon", 101.1, "Ru_on_C", "chemical_catalyst hydrogenation precious_metal",
     "Ammonia_Synthesis Fischer_Tropsch", "supported_metal carbon_support noble_metal", 0.87, 0.83, 550),
    ("Fe_K_Al2O3", 162.0, "Fe_K_Al_Oxide", "chemical_catalyst Fischer_Tropsch base_metal",
     "Fischer_Tropsch Olefin_Synthesis", "promoted_metal potassium_promoter iron_carbide", 0.78, 0.71, 700),
    ("Co_SiO2", 118.9, "Co_on_SiO2", "chemical_catalyst Fischer_Tropsch base_metal",
     "Fischer_Tropsch Wax_Production", "supported_metal silica_support cobalt_metal", 0.84, 0.80, 650),
    ("V2O5_TiO2", 181.9, "V2O5_on_TiO2", "chemical_catalyst oxidation selective_oxidation",
     "SCR_DeNOx Maleic_Anhydride", "metal_oxide vanadia_titania redox_site", 0.86, 0.91, 900),
    ("MoS2", 160.1, "MoS2", "chemical_catalyst hydrodesulfurization transition_metal",
     "HDS HDN Hydrocracking", "transition_metal_sulfide layered_structure edge_site", 0.79, 0.85, 1100),
    ("CeO2_ZrO2", 297.3, "Ce_Zr_Oxide", "chemical_catalyst oxidation three_way_catalyst",
     "CO_Oxidation TWC_Support Oxygen_Storage", "mixed_oxide fluorite_structure oxygen_vacancy", 0.88, 0.87, 1500),
    ("Au_TiO2", 197.0, "Au_on_TiO2", "chemical_catalyst oxidation precious_metal",
     "CO_Oxidation Propylene_Epoxidation PROX", "supported_metal titania_support gold_nanoparticle", 0.82, 0.93, 400),
    ("Ir_Al2O3", 192.2, "Ir_on_Al2O3", "chemical_catalyst reforming precious_metal",
     "Methane_Reforming Dehydrogenation", "supported_metal alumina_support iridium_cluster", 0.89, 0.86, 500),
    ("Cu_CeO2", 143.6, "Cu_on_CeO2", "chemical_catalyst water_gas_shift base_metal",
     "WGS PROX CO_Oxidation", "supported_metal ceria_support copper_cluster", 0.81, 0.84, 450),
    ("Ag_Al2O3", 107.9, "Ag_on_Al2O3", "chemical_catalyst epoxidation precious_metal",
     "Ethylene_Epoxidation Selective_Oxidation", "supported_metal alumina_support silver_particle", 0.90, 0.92, 800),
    ("Ti_Silicalite_TS1", 220.0, "Ti_Si_O", "chemical_catalyst zeolite oxidation",
     "Propylene_Epoxidation Phenol_Hydroxylation", "titanosilicate MFI_framework tetrahedral_Ti", 0.85, 0.94, 1000),
    ("Cr_Al2O3", 152.0, "Cr_on_Al2O3", "chemical_catalyst dehydrogenation base_metal",
     "Propane_Dehydrogenation Isobutane_Dehydrogenation", "supported_metal alumina_support chromia", 0.77, 0.79, 350),
    ("Sn_Pt_Al2O3", 312.8, "Sn_Pt_on_Al2O3", "chemical_catalyst dehydrogenation bimetallic",
     "Propane_Dehydrogenation Light_Alkane_Conversion", "bimetallic_alloy alumina_support electronic_modifier", 0.92, 0.95, 700),
    ("ZSM_22", 195.0, "H_Al_Si_O_TON", "chemical_catalyst zeolite isomerization",
     "Dewaxing Long_Chain_Isomerization", "aluminosilicate TON_framework Bronsted_acid_site", 0.81, 0.88, 1100),
    # === ZEOLITES ===
    ("Beta_Zeolite", 210.0, "H_Al_Si_O_BEA", "zeolite acid_catalyst large_pore",
     "Alkylation Acylation Friedel_Crafts", "aluminosilicate BEA_framework Bronsted_acid_site", 0.87, 0.82, 1300),
    ("Mordenite", 200.0, "H_Al_Si_O_MOR", "zeolite acid_catalyst large_pore",
     "Carbonylation Transalkylation Dewaxing", "aluminosilicate MOR_framework 12MR_channel", 0.83, 0.86, 1400),
    ("MCM_41", 180.0, "Si_O_mesoporous", "zeolite mesoporous support",
     "Large_Molecule_Catalysis Drug_Delivery Support", "mesoporous_silica hexagonal_array high_surface_area", 0.75, 0.70, 2000),
    ("USY_Zeolite", 230.0, "H_Al_Si_O_FAU", "zeolite acid_catalyst FCC",
     "Fluid_Catalytic_Cracking Hydrocracking", "aluminosilicate FAU_framework ultrastable", 0.94, 0.78, 1600),
    ("Ferrierite", 190.0, "H_Al_Si_O_FER", "zeolite acid_catalyst shape_selective",
     "Skeletal_Isomerization Butene_Isomerization", "aluminosilicate FER_framework 10MR_channel", 0.80, 0.91, 1200),
    # === ENZYMES ===
    ("Lipase_E", 420.0, "Ser_Hydrolase_E", "enzyme synthetic_biology lipid_metabolism lipolytic",
     "Triglyceride_Hydrolysis Transesterification Biodiesel", "hydrolase serine_triad alpha_beta_fold", 0.88, 0.92, 60),
    ("Protease_F", 350.0, "Ser_Protease_F", "enzyme synthetic_biology protein_degradation proteolytic",
     "Peptide_Bond_Hydrolysis Casein_Degradation", "hydrolase catalytic_triad subtilisin_fold", 0.91, 0.85, 48),
    ("Peroxidase_G", 440.0, "Heme_Peroxidase_G", "enzyme synthetic_biology oxidation peroxidative",
     "Lignin_Peroxidation Dye_Decolorization ROS_Scavenging", "oxidoreductase heme_iron proximal_histidine", 0.73, 0.78, 30),
    ("Pectinase_H", 380.0, "GH28_Polygalacturonase", "enzyme synthetic_biology biomass_degradation pectinolytic",
     "Pectin_Hydrolysis Juice_Clarification", "hydrolase parallel_beta_helix active_site_Asp", 0.86, 0.90, 56),
    ("Chitinase_I", 460.0, "GH18_Chitinase", "enzyme synthetic_biology chitin_degradation chitinolytic",
     "Chitin_Hydrolysis NAG_Production Biocontrol", "hydrolase TIM_barrel chitin_binding_domain", 0.79, 0.87, 44),
    ("Carbonic_Anhydrase_J", 290.0, "Zn_Metalloenzyme_CA", "enzyme synthetic_biology carbon_capture metalloenzyme",
     "CO2_Hydration Bicarbonate_Formation Carbon_Sequestration", "lyase zinc_active_site beta_sheet_core", 0.94, 0.97, 72),
    ("Nitrogenase_K", 550.0, "Fe_Mo_Cofactor_Nase", "enzyme synthetic_biology nitrogen_fixation metalloenzyme",
     "N2_Fixation Ammonia_Biosynthesis", "oxidoreductase FeMo_cofactor P_cluster", 0.68, 0.75, 24),
    ("Glucose_Oxidase_L", 320.0, "FAD_Oxidase_GOx", "enzyme synthetic_biology biosensor flavoenzyme",
     "Glucose_Oxidation Biosensing H2O2_Generation", "oxidoreductase FAD_cofactor beta_barrel", 0.93, 0.96, 80),
    ("Phytase_M", 410.0, "HAP_Phytase", "enzyme synthetic_biology phosphorus_release phytolytic",
     "Phytate_Hydrolysis Phosphorus_Liberation Feed_Additive", "hydrolase histidine_acid_phosphatase alpha_domain", 0.84, 0.88, 52),
    ("Transglutaminase_N", 370.0, "Cys_Transferase_TG", "enzyme synthetic_biology food_technology crosslinking",
     "Protein_Crosslinking Glutamine_Transfer Meat_Binding", "transferase cysteine_active_site Ig_like_fold", 0.87, 0.91, 64),
    # === CATALYST POISONS / DEACTIVATORS ===
    ("Arsenic_Compound", 74.9, "As_compound", "catalyst_poison deactivator metalloid",
     "", "", 0.0, 0.0, 0),
    ("Phosphorus_Compound", 31.0, "P_compound", "catalyst_poison deactivator nonmetal",
     "", "", 0.0, 0.0, 0),
    ("Chloride_Ion", 35.5, "Cl_minus", "catalyst_poison deactivator halide",
     "", "", 0.0, 0.0, 0),
    ("Silicon_Compound", 28.1, "Si_compound", "catalyst_poison deactivator metalloid",
     "", "", 0.0, 0.0, 0),
    ("Water_Vapor", 18.0, "H2O_g", "environmental_stressor deactivator",
     "", "", 0.0, 0.0, 0),
    ("CO_Poison", 28.0, "CO", "catalyst_poison deactivator small_molecule",
     "", "", 0.0, 0.0, 0),
    ("Nitrogen_Compound", 14.0, "N_compound", "catalyst_poison deactivator nitrogen_bearing",
     "", "", 0.0, 0.0, 0),
    ("Oxidative_Stress", 0.0, "O2_radical", "environmental_stressor deactivator",
     "", "", 0.0, 0.0, 0),
    ("pH_Extreme", 0.0, "acid_base_shock", "environmental_stressor deactivator",
     "", "", 0.0, 0.0, 0),
    ("Sintering_Heat", 0.0, "high_temp_sintering", "environmental_stressor deactivator",
     "", "", 0.0, 0.0, 0),
]

# New interactions: (mol1, mol2, effect, severity)
new_interactions = [
    ("Pt_Al2O3", "Sulfur_Compound", "active_site_poisoning", "high"),
    ("Pt_Al2O3", "Coke_Deposit", "pore_blockage", "moderate"),
    ("Ru_Carbon", "Sulfur_Compound", "surface_poisoning", "high"),
    ("Fe_K_Al2O3", "Sulfur_Compound", "iron_sulfide_formation", "high"),
    ("Co_SiO2", "Sulfur_Compound", "cobalt_sulfide_formation", "high"),
    ("Co_SiO2", "Water_Vapor", "surface_reoxidation", "moderate"),
    ("V2O5_TiO2", "Arsenic_Compound", "active_site_blockage", "high"),
    ("V2O5_TiO2", "Silicon_Compound", "pore_masking", "moderate"),
    ("MoS2", "Coke_Deposit", "active_edge_blockage", "moderate"),
    ("Au_TiO2", "Chloride_Ion", "particle_agglomeration", "moderate"),
    ("Au_TiO2", "Sintering_Heat", "nanoparticle_sintering", "high"),
    ("Ir_Al2O3", "Sulfur_Compound", "surface_poisoning", "high"),
    ("Cu_CeO2", "Chloride_Ion", "copper_leaching", "moderate"),
    ("Cu_CeO2", "Sintering_Heat", "copper_sintering", "high"),
    ("Ag_Al2O3", "Sulfur_Compound", "silver_sulfide_formation", "high"),
    ("Ti_Silicalite_TS1", "Coke_Deposit", "pore_blockage", "moderate"),
    ("Cr_Al2O3", "Coke_Deposit", "active_site_coverage", "high"),
    ("Sn_Pt_Al2O3", "Sulfur_Compound", "active_site_poisoning", "high"),
    ("HZSM_5", "Nitrogen_Compound", "acid_site_neutralization", "moderate"),
    ("Beta_Zeolite", "Coke_Deposit", "pore_blockage", "high"),
    ("Mordenite", "Coke_Deposit", "channel_blockage", "high"),
    ("USY_Zeolite", "Coke_Deposit", "supercage_blockage", "high"),
    ("USY_Zeolite", "Heavy_Metal_Ion", "ion_exchange_poisoning", "moderate"),
    ("Ferrierite", "Coke_Deposit", "channel_blockage", "moderate"),
    ("Lipase_E", "Thermal_Stress", "thermal_denaturation", "high"),
    ("Lipase_E", "Oxidative_Stress", "disulfide_scrambling", "moderate"),
    ("Protease_F", "Heavy_Metal_Ion", "active_site_chelation", "moderate"),
    ("Protease_F", "pH_Extreme", "structural_unfolding", "high"),
    ("Peroxidase_G", "Thermal_Stress", "heme_dissociation", "high"),
    ("Peroxidase_G", "pH_Extreme", "iron_displacement", "moderate"),
    ("Pectinase_H", "Heavy_Metal_Ion", "competitive_inhibition", "low"),
    ("Chitinase_I", "Thermal_Stress", "thermal_unfolding", "moderate"),
    ("Carbonic_Anhydrase_J", "Heavy_Metal_Ion", "zinc_displacement", "high"),
    ("Carbonic_Anhydrase_J", "pH_Extreme", "protonation_shift", "moderate"),
    ("Nitrogenase_K", "Oxidative_Stress", "FeMo_cofactor_damage", "high"),
    ("Nitrogenase_K", "CO_Poison", "competitive_binding", "high"),
    ("Glucose_Oxidase_L", "Heavy_Metal_Ion", "FAD_displacement", "moderate"),
    ("Glucose_Oxidase_L", "Thermal_Stress", "thermal_denaturation", "moderate"),
    ("Phytase_M", "pH_Extreme", "acid_denaturation", "moderate"),
    ("Transglutaminase_N", "Oxidative_Stress", "cysteine_oxidation", "high"),
    ("Cellulase_A", "pH_Extreme", "acid_denaturation", "moderate"),
    ("Laccase_C", "Chloride_Ion", "chloride_inhibition", "moderate"),
    ("Amylase_D", "pH_Extreme", "structural_unfolding", "moderate"),
]

# New similarity links
new_similar = [
    ("Pt_Al2O3", "Ir_Al2O3"),
    ("Ru_Carbon", "Fe_K_Al2O3"),
    ("Co_SiO2", "Fe_K_Al2O3"),
    ("Au_TiO2", "Ag_Al2O3"),
    ("Cu_CeO2", "Cu_ZnO_Al2O3"),
    ("V2O5_TiO2", "CeO2_ZrO2"),
    ("Beta_Zeolite", "HZSM_5"),
    ("Mordenite", "HZSM_5"),
    ("USY_Zeolite", "Beta_Zeolite"),
    ("ZSM_22", "HZSM_5"),
    ("Ferrierite", "ZSM_22"),
    ("MCM_41", "SAPO_34"),
    ("Ti_Silicalite_TS1", "HZSM_5"),
    ("Sn_Pt_Al2O3", "Pt_Al2O3"),
    ("Cr_Al2O3", "Pt_Al2O3"),
    ("Lipase_E", "Protease_F"),
    ("Peroxidase_G", "Laccase_C"),
    ("Pectinase_H", "Cellulase_A"),
    ("Chitinase_I", "Cellulase_A"),
    ("Carbonic_Anhydrase_J", "Nitrogenase_K"),
    ("Glucose_Oxidase_L", "Laccase_C"),
    ("Phytase_M", "Amylase_D"),
    ("Transglutaminase_N", "Lipase_E"),
    ("Arsenic_Compound", "Sulfur_Compound"),
    ("Phosphorus_Compound", "Sulfur_Compound"),
    ("Chloride_Ion", "Heavy_Metal_Ion"),
    ("Water_Vapor", "Thermal_Stress"),
    ("CO_Poison", "Sulfur_Compound"),
    ("Oxidative_Stress", "Thermal_Stress"),
    ("Sintering_Heat", "Thermal_Stress"),
]

out = os.path.join(os.path.dirname(__file__), "molecules.metta")
with open(out, "r") as f:
    original = f.read()

with open(out, "w") as f:
    # Write original content (minus trailing newline)
    f.write(original.rstrip())
    f.write("\n\n")

    # ---- NEW MOLECULE DECLARATIONS ----
    f.write("; ============================================================\n")
    f.write("; EXPANDED KNOWLEDGE BASE — Additional Molecules\n")
    f.write("; ============================================================\n\n")

    f.write("; ---- New Molecule Declarations ----\n")
    for m in new_mols:
        f.write(f"(molecule {m[0]})\n")

    f.write("\n; ---- New Molecular Weights ----\n")
    for m in new_mols:
        f.write(f"(molecular_weight {m[0]} {m[1]})\n")

    f.write("\n; ---- New Chemical Formulas ----\n")
    for m in new_mols:
        f.write(f"(formula {m[0]} {m[2]})\n")

    f.write("\n; ---- New Categories ----\n")
    for m in new_mols:
        f.write(f"(category {m[0]} {m[3]})\n")

    f.write("\n; ---- New Targets ----\n")
    for m in new_mols:
        if m[4]:
            f.write(f"(target {m[0]} {m[4]})\n")

    f.write("\n; ---- New Functional Groups ----\n")
    for m in new_mols:
        if m[5]:
            f.write(f"(functional_group {m[0]} {m[5]})\n")

    f.write("\n; ---- New Activity Scores ----\n")
    for m in new_mols:
        if m[6] > 0:
            f.write(f"(activity_score {m[0]} {m[6]:.2f})\n")

    f.write("\n; ---- New Selectivity ----\n")
    for m in new_mols:
        if m[7] > 0:
            f.write(f"(selectivity {m[0]} {m[7]:.2f})\n")

    f.write("\n; ---- New Stability (hours) ----\n")
    for m in new_mols:
        if m[8] > 0:
            f.write(f"(stability {m[0]} {m[8]})\n")

    f.write("\n; ---- New Similarity Links ----\n")
    for s in new_similar:
        f.write(f"(similar_to {s[0]} {s[1]})\n")

    f.write("\n; ---- New Interactions ----\n")
    for ix in new_interactions:
        f.write(f"(interacts {ix[0]} {ix[1]} {ix[2]} {ix[3]})\n")

    f.write("\n; === END OF EXPANDED KNOWLEDGE BASE ===\n")

print(f"Done! Wrote expanded knowledge base to {out}")
all_names = orig + [m[0] for m in new_mols]
print(f"Total molecules: {len(all_names)}")
print(f"Total interactions: {8 + len(new_interactions)}")
print(f"Total similarity links: {5 + len(new_similar)}")
