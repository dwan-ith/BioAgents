(molecule Aspirin)
(molecular_weight 180.16)
(functional_group "carboxylic acid")
(interacts_with "COX enzyme")
(toxicity_score 0.6)
(bioavailability 0.8)

(molecule Caffeine)
(molecular_weight 194.19)
(functional_group "xanthine")
(interacts_with "Adenosine receptors")
(toxicity_score 0.4)
(bioavailability 0.9)

(molecule Ibuprofen)
(molecular_weight 206.28)
(functional_group "propionic acid")
(interacts_with "COX enzyme")
(toxicity_score 0.7)
(bioavailability 0.8)

(similar_to Aspirin Ibuprofen)
(similar_to Aspirin SalicylicAcid)
(less_toxic Caffeine true)
(less_toxic Aspirin false)

(reaction_possible ?a ?b) :-
    (interacts_with ?a ?target),
    (interacts_with ?b ?target),
    (not (= ?a ?b)).

(find ?compound
  (similar_to ?compound Aspirin)
  (less_toxic ?compound true)
  (category "analgesic"))