<?php
// This file is part of Moodle - https://moodle.org/
//
// Moodle is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// any later version.

defined('MOODLE_INTERNAL') || die();

/**
 * Chaînes françaises du module d’activité Registraire UCKK.
 *
 * @package    mod_uckkarchive
 * @copyright  2026 Univers-Cité King Klown
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

// -----------------------------------------------------------------------------
// Identité du plugin.
// -----------------------------------------------------------------------------

$string['pluginname'] = 'Registraire UCKK';
$string['pluginadministration'] = 'Administration du Registraire UCKK';
$string['modulename'] = 'Registraire UCKK';
$string['modulenameplural'] = 'Registres UCKK';
$string['modulename_help'] = 'L’activité Registraire UCKK conserve les preuves, décisions, travaux de cours, Kristals, éléments de portfolio, synthèses d’intégrité, versions et paquets exportables avec provenance, visibilité, validation et historique de révision.';
$string['modulename_link'] = 'mod/uckkarchive/view';
$string['uckkarchive:addinstance'] = 'Ajouter une nouvelle activité Registraire UCKK';
$string['uckkarchive:view'] = 'Voir le Registraire UCKK';
$string['uckkarchive:additem'] = 'Ajouter un élément de registre';
$string['uckkarchive:validateitem'] = 'Valider un élément de registre';
$string['uckkarchive:reviseitem'] = 'Réviser un élément de registre';
$string['uckkarchive:versionitem'] = 'Versionner un élément de registre';
$string['uckkarchive:viewrestricted'] = 'Voir les éléments de registre restreints';
$string['uckkarchive:export'] = 'Exporter des paquets d’export';

// -----------------------------------------------------------------------------
// Libellés généraux.
// -----------------------------------------------------------------------------

$string['activity'] = 'Activité';
$string['actions'] = 'Actions';
$string['add'] = 'Ajouter';
$string['additem'] = 'Ajouter un élément de registre';
$string['archive'] = 'Registre';
$string['archiveactivity'] = 'Activité du registre';
$string['archiveitem'] = 'Élément de registre';
$string['archiveitems'] = 'Éléments de registre';
$string['archiveitemdetails'] = 'Détails de l’élément de registre';
$string['archiveoverview'] = 'Vue d’ensemble du registre';
$string['archivepolicy'] = 'Politique de registre';
$string['archives'] = 'Registres';
$string['backtoarchive'] = 'Retour au registre';
$string['backtoarchives'] = 'Retour aux registres';
$string['cancel'] = 'Annuler';
$string['close'] = 'Fermer';
$string['confirm'] = 'Confirmer';
$string['continue'] = 'Continuer';
$string['course'] = 'Cours';
$string['created'] = 'Créé';
$string['createdby'] = 'Créé par';
$string['description'] = 'Description';
$string['details'] = 'Détails';
$string['download'] = 'Télécharger';
$string['edit'] = 'Modifier';
$string['empty'] = 'Rien à afficher.';
$string['export'] = 'Exporter';
$string['files'] = 'Fichiers';
$string['filter'] = 'Filtrer';
$string['item'] = 'Élément';
$string['items'] = 'Éléments';
$string['metadata'] = 'Métadonnées';
$string['modified'] = 'Modifié';
$string['modifiedby'] = 'Modifié par';
$string['name'] = 'Nom';
$string['none'] = 'Aucun';
$string['notes'] = 'Notes';
$string['open'] = 'Ouvrir';
$string['owner'] = 'Propriétaire';
$string['preview'] = 'Aperçu';
$string['provenance'] = 'Provenance';
$string['reason'] = 'Raison';
$string['records'] = 'Traces';
$string['restricted'] = 'Restreint';
$string['restricted_integrity'] = 'Restreint à l’intégrité';
$string['revision'] = 'Révision';
$string['revisions'] = 'Révisions';
$string['save'] = 'Enregistrer';
$string['search'] = 'Rechercher';
$string['source'] = 'Source';
$string['status'] = 'Statut';
$string['submit'] = 'Soumettre';
$string['summary'] = 'Résumé';
$string['title'] = 'Titre';
$string['type'] = 'Type';
$string['validation'] = 'Validation';
$string['visibility'] = 'Visibilité';
$string['version'] = 'Version';
$string['versionno'] = 'Version {$a}';
$string['view'] = 'Voir';
$string['viewdetails'] = 'Voir les détails';

// -----------------------------------------------------------------------------
// Formulaire d’instance d’activité.
// -----------------------------------------------------------------------------

$string['archivename'] = 'Nom du registre';
$string['archivename_help'] = 'Nom de cette activité Registraire UCKK.';
$string['archiveintro'] = 'Introduction du registre';
$string['archivecode'] = 'Code du registre';
$string['archivecode_help'] = 'Code interne stable pour ce registre. Utilisez uniquement des lettres, chiffres, traits de soulignement ou traits d’union.';
$string['archivecontext'] = 'Contexte du registre';
$string['archivecontext_help'] = 'Décrivez ce que ce registre doit préserver et qui peut l’utiliser.';
$string['archivepurpose'] = 'Finalité du registre';
$string['archivepurpose_help'] = 'Expliquez pourquoi ce registre existe : preuves, décisions, portfolio, mémoire de cours, Kristals, synthèses d’intégrité ou mémoire institutionnelle.';
$string['defaultvisibility'] = 'Visibilité par défaut';
$string['defaultvisibility_help'] = 'Visibilité appliquée par défaut aux nouveaux éléments, sauf remplacement dans le formulaire de l’élément.';
$string['allowpublicitems'] = 'Autoriser les éléments publics';
$string['allowpublicitems_help'] = 'Autoriser les éléments de registre validés manuellement à devenir publics.';
$string['requirevalidation'] = 'Exiger la validation avant publication';
$string['requirevalidation_help'] = 'Exiger qu’une personne autorisée valide les éléments avant qu’ils soient considérés comme vérifiés ou publics.';
$string['allowkristals'] = 'Autoriser les Kristals';
$string['allowkristals_help'] = 'Autoriser ce registre à stocker des Kristals : fragments distillés d’apprentissage, décision, preuve ou mémoire.';
$string['allowexports'] = 'Autoriser les exports';
$string['allowexports_help'] = 'Autoriser les personnes habilitées à exporter des paquets d’export.';
$string['completionrequirevalidateditem'] = 'L’étudiant doit avoir un élément de registre validé';
$string['completionrequireitem'] = 'L’étudiant doit ajouter un élément de registre';
$string['completionrequirekristal'] = 'L’étudiant doit créer un Kristal';

// -----------------------------------------------------------------------------
// Paramètres.
// -----------------------------------------------------------------------------

$string['settings:general'] = 'Paramètres généraux des registres';
$string['settings:general_desc'] = 'Configurer les valeurs par défaut des Registres UCKK.';
$string['settings:defaultvisibility'] = 'Visibilité de registre par défaut';
$string['settings:defaultvisibility_desc'] = 'Visibilité utilisée par défaut lorsqu’un nouvel élément de registre ne précise pas sa visibilité.';
$string['settings:requirevalidation'] = 'Exiger la validation';
$string['settings:requirevalidation_desc'] = 'Exiger une validation avant que les éléments de registre deviennent vérifiés ou publics.';
$string['settings:allowpublicarchives'] = 'Autoriser les éléments de registre publics';
$string['settings:allowpublicarchives_desc'] = 'Autoriser les éléments de registre à devenir publics après validation manuelle.';
$string['settings:allowrestrictedintegrity'] = 'Autoriser les registres restreints à l’intégrité';
$string['settings:allowrestrictedintegrity_desc'] = 'Autoriser les éléments de registre à être marqués comme restreints aux personnes disposant de capacités d’intégrité ou de registre restreint.';
$string['settings:enablekristals'] = 'Activer les Kristals';
$string['settings:enablekristals_desc'] = 'Activer la création et l’affichage de Kristals dans les Registres UCKK.';
$string['settings:enableexports'] = 'Activer les paquets d’export';
$string['settings:enableexports_desc'] = 'Autoriser les personnes habilitées à générer des paquets d’export.';
$string['settings:retentiondays'] = 'Durée de conservation par défaut';
$string['settings:retentiondays_desc'] = 'Durée de conservation par défaut en jours. Utiliser 0 pour aucune expiration automatique.';
$string['settings:maxexportitems'] = 'Nombre maximal d’éléments par export';
$string['settings:maxexportitems_desc'] = 'Nombre maximal d’éléments de registre inclus dans un paquet d’export.';
$string['settings:provenance'] = 'Paramètres de provenance';
$string['settings:provenance_desc'] = 'Configurer la provenance et le comportement de validation des registres.';
$string['settings:requireprovenance'] = 'Exiger la provenance';
$string['settings:requireprovenance_desc'] = 'Exiger une déclaration de provenance pour chaque élément de registre.';
$string['settings:requirevalidationnotes'] = 'Exiger des notes de validation';
$string['settings:requirevalidationnotes_desc'] = 'Exiger que les validateurs fournissent des notes lors de la validation, du rejet ou de l’invalidation d’un élément.';

// -----------------------------------------------------------------------------
// Formulaire d’élément.
// -----------------------------------------------------------------------------

$string['archiveitemform'] = 'Formulaire d’élément de registre';
$string['itemtitle'] = 'Titre de l’élément';
$string['itemtitle_help'] = 'Titre clair pour l’élément de registre.';
$string['itemsummary'] = 'Résumé de l’élément';
$string['itemsummary_help'] = 'Résumé court et sûr pour le niveau de visibilité choisi.';
$string['itemcontent'] = 'Contenu de l’élément';
$string['itemcontent_help'] = 'Contenu principal du registre. N’incluez pas de détails restreints sauf si la visibilité de l’élément le permet.';
$string['itemtype'] = 'Type d’élément';
$string['itemtype_help'] = 'Choisissez le type qui décrit le mieux l’élément de registre.';
$string['itemstatus'] = 'Statut de l’élément';
$string['itemvisibility'] = 'Visibilité de l’élément';
$string['itemvisibility_help'] = 'Contrôle qui peut voir cet élément de registre. Les éléments restreints à l’intégrité exigent une capacité explicite.';
$string['itemprovenance'] = 'Provenance de l’élément';
$string['itemprovenance_help'] = 'Expliquez d’où vient l’élément, qui l’a produit, ce qui a été transformé et ce qui peut être vérifié.';
$string['itemsource'] = 'Source';
$string['itemsource_help'] = 'Source originale, système, activité, personne, registre ou référence externe de cet élément.';
$string['sourcecomponent'] = 'Composant source';
$string['sourcecomponent_help'] = 'Composant Moodle ayant généré l’élément, si connu.';
$string['sourceid'] = 'ID source';
$string['sourceid_help'] = 'ID de l’enregistrement dans le composant source, si connu.';
$string['sourceurl'] = 'URL source';
$string['sourceurl_help'] = 'URL optionnelle pointant vers la source.';
$string['sourceauthor'] = 'Source ou auteur';
$string['sourceauthor_help'] = 'Personne, groupe, système, activité ou source de registre derrière l’élément.';
$string['sourcedate'] = 'Date de la source';
$string['sourcedate_help'] = 'Date associée à la source originale.';
$string['license'] = 'Licence';
$string['license_help'] = 'Licence ou condition de réutilisation attachée à l’élément, le cas échéant.';
$string['tags'] = 'Étiquettes';
$string['tags_help'] = 'Étiquettes optionnelles séparées par des virgules pour le filtrage et les rapports.';
$string['files_help'] = 'Fichiers attachés à cet élément de registre. Les fichiers héritent de la visibilité de l’élément sauf si un service applique une règle plus stricte.';
$string['prooffiles'] = 'Fichiers de preuve';
$string['decisionattachments'] = 'Pièces jointes de décision';
$string['minutesfiles'] = 'Fichiers de procès-verbal';
$string['kristalfiles'] = 'Fichiers de Kristal';
$string['portfoliofiles'] = 'Fichiers de portfolio';
$string['integrityexports'] = 'Exports d’intégrité';
$string['addarchiveitem'] = 'Ajouter un élément de registre';
$string['editarchiveitem'] = 'Modifier l’élément de registre';
$string['archiveitemsaved'] = 'Élément de registre enregistré.';
$string['archiveitemcreated'] = 'Élément de registre créé.';
$string['archiveitemupdated'] = 'Élément de registre mis à jour.';
$string['cannotadditem'] = 'Vous ne pouvez pas ajouter d’éléments de registre ici.';
$string['cannotedititem'] = 'Vous ne pouvez pas modifier cet élément de registre.';
$string['cannotviewitem'] = 'Vous ne pouvez pas voir cet élément de registre.';
$string['missingarchiveitem'] = 'Élément de registre introuvable.';
$string['invaliditemtype'] = 'Type d’élément de registre invalide.';
$string['invaliditemstatus'] = 'Statut d’élément de registre invalide.';
$string['invaliditemvisibility'] = 'Visibilité d’élément de registre invalide.';
$string['provenancerequired'] = 'Une déclaration de provenance est requise.';
$string['contentorsourcefilesrequired'] = 'Ajoutez du contenu, une URL source ou au moins un fichier.';

// -----------------------------------------------------------------------------
// Kristals.
// -----------------------------------------------------------------------------

$string['kristal'] = 'Kristal';
$string['kristals'] = 'Kristals';
$string['kristalform'] = 'Formulaire de Kristal';
$string['addkristal'] = 'Ajouter un Kristal';
$string['editkristal'] = 'Modifier le Kristal';
$string['kristaltitle'] = 'Titre du Kristal';
$string['kristaltitle_help'] = 'Titre court de ce Kristal.';
$string['kristalstatement'] = 'Énoncé du Kristal';
$string['kristalstatement_help'] = 'Énoncé distillé d’apprentissage, décision, preuve, intuition ou mémoire.';
$string['kristalcontext'] = 'Contexte du Kristal';
$string['kristalcontext_help'] = 'Expliquez le contexte à partir duquel ce Kristal a été distillé.';
$string['kristalproof'] = 'Preuve du Kristal';
$string['kristalproof_help'] = 'Preuve ou références soutenant le Kristal.';
$string['kristaltype'] = 'Type de Kristal';
$string['kristalvisibility'] = 'Visibilité du Kristal';
$string['kristalcreated'] = 'Kristal créé.';
$string['kristalupdated'] = 'Kristal mis à jour.';
$string['kristalempty'] = 'Aucun Kristal disponible.';
$string['cannotaddkristal'] = 'Vous ne pouvez pas ajouter de Kristals ici.';
$string['cannoteditkristal'] = 'Vous ne pouvez pas modifier ce Kristal.';
$string['cannotviewkristal'] = 'Vous ne pouvez pas voir ce Kristal.';
$string['invalidkristaltype'] = 'Type de Kristal invalide.';

// -----------------------------------------------------------------------------
// Validation.
// -----------------------------------------------------------------------------

$string['validate'] = 'Valider';
$string['validateitem'] = 'Valider l’élément de registre';
$string['validationform'] = 'Formulaire de validation';
$string['validationstate'] = 'État de validation';
$string['validationnotes'] = 'Notes de validation';
$string['validationnotes_help'] = 'Expliquez la décision de validation, l’incertitude, les corrections requises ou la raison du rejet.';
$string['validationdecision'] = 'Décision de validation';
$string['validationdecision_help'] = 'Choisissez comment cet élément de registre doit être traité après revue.';
$string['validatedby'] = 'Validé par';
$string['timevalidated'] = 'Moment de validation';
$string['archiveitemvalidated'] = 'Élément de registre validé.';
$string['archiveitemrejected'] = 'Élément de registre rejeté.';
$string['archiveiteminvalidated'] = 'Élément de registre invalidé.';
$string['archiveitemcorrectionrequired'] = 'Correction requise pour l’élément de registre.';
$string['archiveitemcontested'] = 'Élément de registre contesté.';
$string['cannotvalidateitem'] = 'Vous ne pouvez pas valider cet élément de registre.';
$string['validationrequiresnotes'] = 'Des notes de validation sont requises pour cette décision.';
$string['manualvalidationrequired'] = 'Validation manuelle requise';
$string['publicvalidationrequired'] = 'Les éléments de registre publics doivent être validés manuellement.';
$string['restrictedvalidationrequired'] = 'Les éléments de registre restreints à l’intégrité exigent une validation explicite.';

$string['validationdecision:validate'] = 'Valider';
$string['validationdecision:reject'] = 'Rejeter';
$string['validationdecision:correction_required'] = 'Correction requise';
$string['validationdecision:contest'] = 'Contester';
$string['validationdecision:invalidate'] = 'Invalider';

// -----------------------------------------------------------------------------
// Révision et versioning.
// -----------------------------------------------------------------------------

$string['revise'] = 'Réviser';
$string['reviseitem'] = 'Réviser l’élément de registre';
$string['revisionform'] = 'Formulaire de révision';
$string['revisionreason'] = 'Raison de la révision';
$string['revisionreason_help'] = 'Expliquez pourquoi cette révision est nécessaire. L’historique du registre doit rester traçable.';
$string['revisionnotes'] = 'Notes de révision';
$string['revisioncreated'] = 'Révision créée.';
$string['archiveitemrevised'] = 'Élément de registre révisé.';
$string['previousversion'] = 'Version précédente';
$string['currentversion'] = 'Version actuelle';
$string['versionhistory'] = 'Historique des versions';
$string['versionrecord'] = 'Trace de version';
$string['cannotreviseitem'] = 'Vous ne pouvez pas réviser cet élément de registre.';
$string['cannotversionitem'] = 'Vous ne pouvez pas créer de trace de version pour cet élément.';
$string['revisionrequiresreason'] = 'Une raison de révision est requise.';
$string['revisionnonsovereignnotice'] = 'Une révision préserve l’historique du registre. Elle ne doit pas effacer silencieusement les preuves ou la provenance.';

// -----------------------------------------------------------------------------
// Export.
// -----------------------------------------------------------------------------

$string['exportarchive'] = 'Exporter le registre';
$string['exportform'] = 'Formulaire d’export';
$string['exportpackage'] = 'Paquet d’export';
$string['exportpackages'] = 'Paquets d’export';
$string['exportformat'] = 'Format d’export';
$string['exportscope'] = 'Portée de l’export';
$string['exportvisibility'] = 'Visibilité de l’export';
$string['exportreason'] = 'Raison de l’export';
$string['exportreason_help'] = 'Expliquez pourquoi cet export du registre est nécessaire.';
$string['exportincludeproofs'] = 'Inclure les fichiers de preuve';
$string['exportincludeprovenance'] = 'Inclure la provenance';
$string['exportincludehistory'] = 'Inclure l’historique des révisions';
$string['exportincludeintegrity'] = 'Inclure les synthèses d’intégrité';
$string['exportredactrestricted'] = 'Caviarder les détails restreints';
$string['exportredactrestricted_help'] = 'Retirer ou résumer les détails restreints d’intégrité dans le paquet d’export, sauf si la personne dispose d’une permission explicite.';
$string['exportgenerated'] = 'Export généré.';
$string['archiveitemexported'] = 'Élément de registre exporté.';
$string['cannotexportarchive'] = 'Vous ne pouvez pas exporter ce registre.';
$string['cannotexportitem'] = 'Vous ne pouvez pas exporter cet élément de registre.';
$string['exportrequiresreason'] = 'Une raison d’export est requise.';
$string['exportempty'] = 'Aucun paquet d’export disponible.';
$string['downloadexport'] = 'Télécharger l’export';
$string['exportqueued'] = 'Export mis en file.';
$string['exportfailed'] = 'Échec de l’export.';
$string['exportsucceeded'] = 'Export terminé.';

$string['exportformat:json'] = 'JSON';
$string['exportformat:zip'] = 'Paquet ZIP';
$string['exportformat:csv'] = 'CSV';
$string['exportformat:pdf'] = 'Résumé PDF';
$string['exportscope:item'] = 'Élément unique';
$string['exportscope:archive'] = 'Registre complet';
$string['exportscope:course'] = 'Registre de cours';
$string['exportscope:user'] = 'Registre de portfolio utilisateur';
$string['exportscope:integrity'] = 'Registre d’intégrité';

// -----------------------------------------------------------------------------
// Types d’éléments.
// -----------------------------------------------------------------------------

$string['itemtype:proof'] = 'Preuve';
$string['itemtype:decision'] = 'Décision';
$string['itemtype:course_work'] = 'Travail de cours';
$string['itemtype:challenge_result'] = 'Résultat de défi';
$string['itemtype:assembly_minutes'] = 'Procès-verbal d’assemblée';
$string['itemtype:integrity_case_summary'] = 'Synthèse de dossier d’intégrité';
$string['itemtype:kristal'] = 'Kristal';
$string['itemtype:reflection'] = 'Réflexion';
$string['itemtype:portfolio_item'] = 'Élément de portfolio';
$string['itemtype:version_record'] = 'Trace de version';
$string['itemtype:archive_item'] = 'Élément de registre';
// -----------------------------------------------------------------------------
// Types de Kristals.
// -----------------------------------------------------------------------------

$string['kristaltype:learning'] = 'Kristal d’apprentissage';
$string['kristaltype:decision'] = 'Kristal de décision';
$string['kristaltype:proof'] = 'Kristal de preuve';
$string['kristaltype:reflection'] = 'Kristal de réflexion';
$string['kristaltype:method'] = 'Kristal de méthode';
$string['kristaltype:governance'] = 'Kristal de gouvernance';
$string['kristaltype:integrity'] = 'Kristal d’intégrité';
$string['kristaltype:memory'] = 'Kristal de mémoire';

// -----------------------------------------------------------------------------
// Types de preuves.
// -----------------------------------------------------------------------------

$string['prooftype'] = 'Type de preuve';
$string['prooftype:text'] = 'Texte';
$string['prooftype:file'] = 'Fichier';
$string['prooftype:url'] = 'URL';
$string['prooftype:dataset'] = 'Jeu de données';
$string['prooftype:image'] = 'Image';
$string['prooftype:video'] = 'Vidéo';
$string['prooftype:testimony'] = 'Témoignage';
$string['prooftype:observation'] = 'Observation';
$string['prooftype:ai_log'] = 'Journal IA';
$string['prooftype:decision_record'] = 'Compte rendu de décision';
$string['prooftype:archive_item'] = 'Élément de registre';

// -----------------------------------------------------------------------------
// Statuts.
// -----------------------------------------------------------------------------

$string['status:draft'] = 'Brouillon';
$string['status:active'] = 'Actif';
$string['status:hidden'] = 'Masqué';
$string['status:pending'] = 'En attente';
$string['status:pending_review'] = 'En attente de revue';
$string['status:validated'] = 'Validé';
$string['status:rejected'] = 'Rejeté';
$string['status:correction_required'] = 'Correction requise';
$string['status:contested'] = 'Contesté';
$string['status:invalidated'] = 'Invalidé';
$string['status:closed'] = 'Fermé';
$string['status:archived'] = 'Classé';
$string['status:cancelled'] = 'Annulé';

$string['statuslabel:draft'] = 'Brouillon';
$string['statuslabel:active'] = 'Actif';
$string['statuslabel:hidden'] = 'Masqué';
$string['statuslabel:pending'] = 'En attente';
$string['statuslabel:pendingreview'] = 'En attente de revue';
$string['statuslabel:validated'] = 'Validé';
$string['statuslabel:rejected'] = 'Rejeté';
$string['statuslabel:correctionrequired'] = 'Correction requise';
$string['statuslabel:contested'] = 'Contesté';
$string['statuslabel:invalidated'] = 'Invalidé';
$string['statuslabel:closed'] = 'Fermé';
$string['statuslabel:archived'] = 'Classé';
$string['statuslabel:cancelled'] = 'Annulé';

// -----------------------------------------------------------------------------
// Visibilité.
// -----------------------------------------------------------------------------

$string['visibility:private'] = 'Privée';
$string['visibility:user'] = 'Utilisateur';
$string['visibility:group'] = 'Groupe';
$string['visibility:course'] = 'Cours';
$string['visibility:cohort'] = 'Cohorte';
$string['visibility:program'] = 'Programme';
$string['visibility:institution'] = 'Institution';
$string['visibility:institutional'] = 'Institutionnelle';
$string['visibility:public'] = 'Publique';
$string['visibility:restricted'] = 'Restreinte';
$string['visibility:restricted_integrity'] = 'Restreinte à l’intégrité';
$string['visibility:hidden'] = 'Masquée';
$string['visibility:archived'] = 'Classée';

$string['visibility_help:private'] = 'Visible uniquement par les propriétaires et réviseurs autorisés.';
$string['visibility_help:course'] = 'Visible dans le contexte du cours pour les personnes autorisées.';
$string['visibility_help:program'] = 'Visible dans le programme UCKK lié.';
$string['visibility_help:institution'] = 'Visible aux personnes institutionnelles autorisées.';
$string['visibility_help:public'] = 'Publique uniquement après validation manuelle.';
$string['visibility_help:restricted_integrity'] = 'Visible uniquement par les personnes disposant des permissions d’intégrité ou de registre restreint.';

// -----------------------------------------------------------------------------
// Provenance.
// -----------------------------------------------------------------------------

$string['provenance:human'] = 'Humaine';
$string['provenance:ai_assisted'] = 'Assistée par IA';
$string['provenance:imported'] = 'Importée';
$string['provenance:system'] = 'Système';
$string['provenance:archive'] = 'Registre';
$string['provenance:assembly'] = 'Assemblée';
$string['provenance:challenge'] = 'Défi';
$string['provenance:integrity'] = 'Intégrité';

$string['provenancehash'] = 'Hash de provenance';
$string['provenancehash_help'] = 'Hash optionnel utilisé pour détecter ou documenter les changements de provenance.';
$string['provenancepanel'] = 'Panneau de provenance';
$string['provenancesource'] = 'Source de provenance';
$string['provenancestatement'] = 'Déclaration de provenance';
$string['provenancestatement_help'] = 'Expliquez l’origine, l’auteur, les transformations, l’incertitude et le chemin de vérification.';
$string['provenanceverified'] = 'Provenance vérifiée';
$string['provenanceunverified'] = 'Provenance non vérifiée';
$string['provenancewarning'] = 'Avertissement de provenance';

// -----------------------------------------------------------------------------
// États de validation.
// -----------------------------------------------------------------------------

$string['validationstate:unverified'] = 'Non vérifié';
$string['validationstate:human_reviewed'] = 'Revu humainement';
$string['validationstate:verified'] = 'Vérifié';
$string['validationstate:contested'] = 'Contesté';
$string['validationstate:invalidated'] = 'Invalidé';
$string['validationstate:archived'] = 'Classé';

$string['validation:unverified'] = 'Non vérifié';
$string['validation:human_reviewed'] = 'Revu humainement';
$string['validation:verified'] = 'Vérifié';
$string['validation:contested'] = 'Contesté';
$string['validation:invalidated'] = 'Invalidé';
$string['validation:archived'] = 'Classé';

// -----------------------------------------------------------------------------
// Politiques de registre.
// -----------------------------------------------------------------------------

$string['archivepolicy:none'] = 'Aucune politique de registre';
$string['archivepolicy:summary'] = 'Registre synthétique';
$string['archivepolicy:full'] = 'Registre complet';
$string['archivepolicy:restricted_integrity'] = 'Registre restreint à l’intégrité';
$string['archivepolicy:portfolio'] = 'Registre de portfolio';
$string['archivepolicy:institutional_memory'] = 'Mémoire institutionnelle';

// -----------------------------------------------------------------------------
// Pages et panneaux.
// -----------------------------------------------------------------------------

$string['archiveview'] = 'Vue du registre';
$string['archiveviewempty'] = 'Aucun élément de registre n’est disponible pour cette vue.';
$string['archiveitemcard'] = 'Carte d’élément de registre';
$string['kristalcard'] = 'Carte de Kristal';
$string['proofcard'] = 'Carte de preuve';
$string['validationpanel'] = 'Panneau de validation';
$string['archiveactions'] = 'Actions de registre';
$string['itemactions'] = 'Actions de l’élément';
$string['kristalactions'] = 'Actions du Kristal';
$string['validationactions'] = 'Actions de validation';
$string['exportactions'] = 'Actions d’export';
$string['viewarchiveitem'] = 'Voir l’élément de registre';
$string['viewkristal'] = 'Voir le Kristal';
$string['viewprovenance'] = 'Voir la provenance';
$string['viewrevisionhistory'] = 'Voir l’historique des révisions';
$string['viewvalidation'] = 'Voir la validation';
$string['viewexport'] = 'Voir l’export';
$string['emptyarchive'] = 'Ce registre ne contient aucun élément visible.';
$string['emptykristals'] = 'Ce registre ne contient aucun Kristal visible.';
$string['emptyproofs'] = 'Aucune trace de preuve disponible.';
$string['emptyrevisions'] = 'Aucune révision disponible.';
$string['emptyexports'] = 'Aucun export disponible.';
$string['restrictednotice'] = 'Cet élément contient des données de registre restreintes.';
$string['publicnotice'] = 'La visibilité publique d’un élément exige une validation manuelle.';
$string['archivenonsovereignnotice'] = 'Les traces de registre préservent la mémoire et les preuves. La validation, les décisions d’intégrité, la visibilité publique et les exports exigent une revue humaine autorisée.';
$string['archivegovernancenotice'] = 'Le Registraire UCKK préserve les preuves, décisions, Kristals, portfolios et historiques de version. Elle ne doit pas servir à effacer silencieusement des preuves ou à contourner la revue d’intégrité.';

// -----------------------------------------------------------------------------
// Messages de contrôleurs.
// -----------------------------------------------------------------------------

$string['invalidarchiveaction'] = 'Action de registre invalide.';
$string['invalidvalidationaction'] = 'Action de validation invalide.';
$string['invalidexportaction'] = 'Action d’export invalide.';
$string['invalidrevisionaction'] = 'Action de révision invalide.';
$string['invalidvisibility'] = 'Visibilité invalide.';
$string['invalidstatus'] = 'Statut invalide.';
$string['invalidprovenance'] = 'Provenance invalide.';
$string['cannotviewarchive'] = 'Vous ne pouvez pas voir ce registre.';
$string['cannotviewrestricted'] = 'Vous ne pouvez pas voir les données de registre restreintes.';
$string['cannotmanagearchive'] = 'Vous ne pouvez pas gérer ce registre.';
$string['cannotdeleteitem'] = 'Vous ne pouvez pas supprimer cet élément de registre.';
$string['deleteitemnotallowed'] = 'Les éléments de registre doivent être révisés ou invalidés, et non supprimés silencieusement.';
$string['itemnotfound'] = 'Élément de registre introuvable.';
$string['archivenotfound'] = 'Registre introuvable.';
$string['kristalnotfound'] = 'Kristal introuvable.';
$string['exportnotfound'] = 'Paquet d’export introuvable.';
$string['nopermission'] = 'Vous n’avez pas la permission d’effectuer cette action de registre.';

// -----------------------------------------------------------------------------
// Événements.
// -----------------------------------------------------------------------------

$string['eventarchiveitemcreated'] = 'Élément de registre créé';
$string['eventarchiveitemvalidated'] = 'Élément de registre validé';
$string['eventarchiveitemrevised'] = 'Élément de registre révisé';
$string['eventarchiveitemexported'] = 'Élément de registre exporté';
$string['eventkristalcreated'] = 'Kristal créé';
$string['eventkristalupdated'] = 'Kristal mis à jour';
$string['eventarchiveviewed'] = 'Registre consulté';
$string['eventarchiveitemviewed'] = 'Élément de registre consulté';
$string['eventexportgenerated'] = 'Export généré';

// -----------------------------------------------------------------------------
// Tâches planifiées.
// -----------------------------------------------------------------------------

$string['task:validate_pending_items'] = 'Valider les éléments de registre en attente';
$string['task:generate_archive_exports'] = 'Générer les exports du registre';
$string['task:cleanup_expired_exports'] = 'Nettoyer les exports du registre expirés';

// -----------------------------------------------------------------------------
// Services externes et Ajax.
// -----------------------------------------------------------------------------

$string['service:get_archive_view'] = 'Obtenir la vue de registre';
$string['service:get_archive_item'] = 'Obtenir l’élément de registre';
$string['service:save_archive_item'] = 'Enregistrer l’élément de registre';
$string['service:validate_archive_item'] = 'Valider l’élément de registre';
$string['service:revise_archive_item'] = 'Réviser l’élément de registre';
$string['service:create_kristal'] = 'Créer un Kristal';
$string['service:generate_export'] = 'Générer un export du registre';

$string['archive:refreshing'] = 'Actualisation du registre…';
$string['archive:refreshed'] = 'Registre actualisé.';
$string['archive:refreshfailed'] = 'Impossible d’actualiser le registre.';
$string['archive:saving'] = 'Enregistrement de l’élément de registre…';
$string['archive:saved'] = 'Élément de registre enregistré.';
$string['archive:savefailed'] = 'Impossible d’enregistrer l’élément de registre.';
$string['archive:validating'] = 'Validation de l’élément de registre…';
$string['archive:validated'] = 'Élément de registre validé.';
$string['archive:validationfailed'] = 'Impossible de valider l’élément de registre.';
$string['archive:exporting'] = 'Génération de l’export du registre…';
$string['archive:exported'] = 'Export généré.';
$string['archive:exportfailed'] = 'Impossible de générer l’export du registre.';

$string['kristal:refreshing'] = 'Actualisation du Kristal…';
$string['kristal:refreshed'] = 'Kristal actualisé.';
$string['kristal:refreshfailed'] = 'Impossible d’actualiser le Kristal.';
$string['kristal:saving'] = 'Enregistrement du Kristal…';
$string['kristal:saved'] = 'Kristal enregistré.';
$string['kristal:savefailed'] = 'Impossible d’enregistrer le Kristal.';

// -----------------------------------------------------------------------------
// Achèvement.
// -----------------------------------------------------------------------------

$string['completiondetail:items'] = 'Ajouter un élément de registre';
$string['completiondetail:validateditems'] = 'Avoir un élément de registre validé';
$string['completiondetail:kristals'] = 'Créer un Kristal';
$string['completionitems'] = 'Éléments de registre requis';
$string['completionvalidateditems'] = 'Éléments de registre validés requis';
$string['completionkristals'] = 'Kristals requis';

// -----------------------------------------------------------------------------
// Confidentialité.
// -----------------------------------------------------------------------------

$string['privacy:metadata'] = 'L’activité Registraire UCKK stocke des traces de registre, preuves, provenances, décisions de validation, révisions, Kristals et traces d’export.';
$string['privacy:metadata:uckkarchive'] = 'Paramètres de l’instance d’activité Registraire.';
$string['privacy:metadata:uckkarchive_item'] = 'Éléments de registre créés ou validés par des utilisateurs.';
$string['privacy:metadata:uckkarchive_item:userid'] = 'L’utilisateur associé à l’élément de registre.';
$string['privacy:metadata:uckkarchive_item:createdby'] = 'L’utilisateur qui a créé l’élément de registre.';
$string['privacy:metadata:uckkarchive_item:modifiedby'] = 'L’utilisateur qui a modifié l’élément de registre en dernier.';
$string['privacy:metadata:uckkarchive_item:title'] = 'Le titre de l’élément de registre.';
$string['privacy:metadata:uckkarchive_item:summary'] = 'Le résumé de l’élément de registre.';
$string['privacy:metadata:uckkarchive_item:content'] = 'Le contenu de l’élément de registre.';
$string['privacy:metadata:uckkarchive_item:status'] = 'Le statut de l’élément de registre.';
$string['privacy:metadata:uckkarchive_item:visibility'] = 'La visibilité de l’élément de registre.';
$string['privacy:metadata:uckkarchive_item:metadata'] = 'Les métadonnées supplémentaires de l’élément de registre.';
$string['privacy:metadata:uckkarchive_kristal'] = 'Traces de Kristals créées à partir d’éléments de registre ou de preuves d’apprentissage.';
$string['privacy:metadata:uckkarchive_proof'] = 'Traces de preuve associées aux éléments de registre.';
$string['privacy:metadata:uckkarchive_prov'] = 'Traces de provenance associées aux éléments de registre.';
$string['privacy:metadata:uckkarchive_rev'] = 'Traces de révision associées aux éléments de registre.';
$string['privacy:metadata:uckkarchive_export'] = 'Traces de paquets d’export.';
$string['privacy:metadata:files'] = 'Fichiers attachés aux éléments de registre, preuves, décisions, procès-verbaux, Kristals, portfolios ou exports d’intégrité.';
$string['privacy:path:archives'] = 'Traces du Registraire UCKK';
$string['privacy:path:kristals'] = 'Kristals du Registraire UCKK';
$string['privacy:path:proofs'] = 'Preuves du Registraire UCKK';
$string['privacy:path:revisions'] = 'Révisions du Registraire UCKK';
$string['privacy:path:exports'] = 'Exports du Registraire UCKK';

// -----------------------------------------------------------------------------
// Sauvegarde et restauration.
// -----------------------------------------------------------------------------

$string['backupincludeitems'] = 'Inclure les éléments de registre';
$string['backupincludeproofs'] = 'Inclure les fichiers de preuve';
$string['backupincludekristals'] = 'Inclure les Kristals';
$string['backupincludeprovenance'] = 'Inclure la provenance';
$string['backupincluderevisions'] = 'Inclure l’historique des révisions';
$string['restorearchiveitems'] = 'Restaurer les éléments de registre';

// -----------------------------------------------------------------------------
// Erreurs.
// -----------------------------------------------------------------------------

$string['error:missingcontext'] = 'Contexte de registre manquant.';
$string['error:missingcourse'] = 'Cours manquant.';
$string['error:missingcm'] = 'Module de cours manquant.';
$string['error:missingitem'] = 'Élément de registre manquant.';
$string['error:missingarchive'] = 'Registre manquant.';
$string['error:missingkristal'] = 'Kristal manquant.';
$string['error:missingexport'] = 'Paquet d’export manquant.';
$string['error:invalidjson'] = 'Métadonnées JSON invalides.';
$string['error:invalidsource'] = 'Référence source invalide.';
$string['error:invalidfilearea'] = 'Zone de fichiers de registre invalide.';
$string['error:restricted'] = 'Cet élément de registre est restreint.';
$string['error:publicrequiresvalidation'] = 'Les éléments de registre publics exigent une validation manuelle.';
$string['error:cannotautomatevalidation'] = 'La validation de registre ne peut pas être automatisée.';
$string['error:cannotdeletehistory'] = 'L’historique du registre ne peut pas être supprimé silencieusement.';
$string['error:exporttoolarge'] = 'Ce paquet d’export est trop volumineux.';
$string['error:nothingtoexport'] = 'Il n’y a rien à exporter.';

// -----------------------------------------------------------------------------
// Zones de fichiers.
// -----------------------------------------------------------------------------

$string['filearea:proof_files'] = 'Fichiers de preuve';
$string['filearea:decision_attachments'] = 'Pièces jointes de décision';
$string['filearea:minutes_files'] = 'Fichiers de procès-verbal';
$string['filearea:kristal_files'] = 'Fichiers de Kristal';
$string['filearea:portfolio_files'] = 'Fichiers de portfolio';
$string['filearea:integrity_exports'] = 'Exports d’intégrité';
$string['filearea:item_content'] = 'Contenu d’élément de registre';
$string['filearea:export_packages'] = 'Paquets d’export';

// -----------------------------------------------------------------------------
// Rapports et filtres.
// -----------------------------------------------------------------------------

$string['filter:itemtype'] = 'Filtrer par type d’élément';
$string['filter:status'] = 'Filtrer par statut';
$string['filter:visibility'] = 'Filtrer par visibilité';
$string['filter:validationstate'] = 'Filtrer par état de validation';
$string['filter:provenance'] = 'Filtrer par provenance';
$string['filter:createdby'] = 'Filtrer par créateur';
$string['filter:datefrom'] = 'Date de début';
$string['filter:dateto'] = 'Date de fin';
$string['report:archiveproduction'] = 'Production de registres';
$string['report:validateditems'] = 'Éléments validés';
$string['report:pendingitems'] = 'Éléments en attente';
$string['report:restricteditems'] = 'Éléments restreints';
$string['report:exports'] = 'Exports';

// -----------------------------------------------------------------------------
// UI divers.
// -----------------------------------------------------------------------------

$string['confirmvalidate'] = 'Valider cet élément de registre ?';
$string['confirmreject'] = 'Rejeter cet élément de registre ?';
$string['confirminvalidate'] = 'Invalider cet élément de registre ?';
$string['confirmrevision'] = 'Créer une nouvelle révision pour cet élément de registre ?';
$string['confirmexport'] = 'Générer cet export du registre ?';
$string['confirmpublicvisibility'] = 'Rendre cet élément de registre public après validation ?';
$string['yesvalidate'] = 'Oui, valider';
$string['yesreject'] = 'Oui, rejeter';
$string['yesinvalidate'] = 'Oui, invalider';
$string['yesrevise'] = 'Oui, réviser';
$string['yesexport'] = 'Oui, exporter';

// -----------------------------------------------------------------------------
// Chaînes ajoutées depuis l’audit des chaînes Moodle.
// -----------------------------------------------------------------------------

// Compléments ajoutés depuis l’audit.
$string['action:done'] = 'Action terminée.';
$string['action:failed'] = 'L’action a échoué.';
$string['action:running'] = 'Action en cours…';
$string['aiassistancemustbedisclosed'] = 'L’assistance par IA doit être déclarée.';
$string['aiassisted'] = 'Assisté par IA';
$string['aigovernance'] = 'Gouvernance de l’IA';
$string['ailog'] = 'Journal IA';
$string['ailogrequired'] = 'Le journal IA est requis.';
$string['aimetadatarequired'] = 'Les métadonnées IA sont requises.';
$string['ainonsovereignnotice'] = 'L’IA fournit une aide non souveraine : elle ne remplace ni l’autorité humaine, ni la validation, ni la décision institutionnelle.';
$string['aipolicy'] = 'Politique d’utilisation de l’IA';
$string['all'] = 'Tous';
$string['allowailogs'] = 'Autoriser les journaux IA';
$string['allowarchiveitems'] = 'Autoriser les éléments de registre';
$string['allowcontestation'] = 'Autoriser la contestation';
$string['allowportfolioitems'] = 'Autoriser les éléments de portfolio';
$string['allowproofs'] = 'Autoriser les preuves';
$string['archivistnotes'] = 'Notes du responsable du registre';
$string['atleastonearchivetypeenabled'] = 'Au moins un type de registre doit être activé.';
$string['backtoarchiveitem'] = 'Retour à l’élément de registre';
$string['badgekeys'] = 'Clés de badges';
$string['cancelexport'] = 'Annuler l’export';
$string['cancelexportbody'] = 'Voulez-vous annuler cet export du registre ?';
$string['canonref'] = 'Référence canonique';
$string['canonreference'] = 'Référence canonique';
$string['competencycodes'] = 'Codes de compétences';
$string['completionarchiveexported_desc'] = 'L’étudiant doit exporter un registre.';
$string['completionarchivestate_desc'] = 'L’étudiant doit atteindre l’état de registre requis.';
$string['completionarchivevalidated_desc'] = 'L’étudiant doit faire valider un registre.';
$string['completionitemadded_desc'] = 'L’étudiant doit ajouter un élément de registre.';
$string['completionitemvalidated_desc'] = 'L’étudiant doit faire valider un élément de registre.';
$string['completionkristalcreated_desc'] = 'L’étudiant doit créer un Kristal.';
$string['confirmarchiveaction'] = 'Confirmer l’action de registre';
$string['confirmarchiveactionbody'] = 'Voulez-vous vraiment effectuer cette action sur le registre ?';
$string['confirmexportbody'] = 'Voulez-vous générer cet export du registre ?';
$string['confirmkristalsubmit'] = 'Soumettre le Kristal';
$string['confirmkristalsubmitbody'] = 'Voulez-vous soumettre ce Kristal pour enregistrement ou validation ?';
$string['confirmrestrictedexportbody'] = 'Cet export peut inclure des données restreintes. Confirmez que vous êtes autorisé à le générer.';
$string['content'] = 'Contenu';
$string['contestabilitydays'] = 'Délai de contestation en jours';
$string['contestabilitydaysinvalid'] = 'Le délai de contestation doit être un nombre de jours valide.';
$string['contestationallowed'] = 'Contestation autorisée';
$string['contextverified'] = 'Contexte vérifié';
$string['correctionrequiresrevision'] = 'Une correction exige une nouvelle révision.';
$string['createversionrecord'] = 'Créer un enregistrement de version';
$string['currentstatus'] = 'Statut actuel';
$string['currentvalidationstate'] = 'État de validation actuel';
$string['currentvisibility'] = 'Visibilité actuelle';
$string['defaultaipolicy'] = 'Politique IA par défaut';
$string['defaultitemtype'] = 'Type d’élément par défaut';
$string['defaultprovenance'] = 'Provenance par défaut';
$string['defaultvalidationstate'] = 'État de validation par défaut';
$string['ethicalnotes'] = 'Notes éthiques';
$string['evidencepolicy'] = 'Politique de preuve';
$string['evidencerelationverified'] = 'Relation de preuve vérifiée';
$string['forcerevisions'] = 'Forcer les révisions';
$string['format'] = 'Format';
$string['generatedat'] = 'Généré le {$a}';
$string['includefilesinexports'] = 'Inclure les fichiers dans les exports';
$string['includerevisionsinexports'] = 'Inclure les révisions dans les exports';
$string['integrityandai'] = 'Intégrité et IA';
$string['integritynotes'] = 'Notes d’intégrité';
$string['integritynotesrequired'] = 'Les notes d’intégrité sont requises.';
$string['integrityrequired'] = 'Intégrité requise';
$string['integrityreview'] = 'Révision d’intégrité';
$string['integritysummary'] = 'Résumé d’intégrité';
$string['integritysummaryrequired'] = 'Le résumé d’intégrité est requis.';
$string['invalidarchivecode'] = 'Code de registre invalide.';
$string['invalidexportformat'] = 'Format d’export invalide.';
$string['invalidexportmode'] = 'Mode d’export invalide.';
$string['invalidexportscope'] = 'Portée d’export invalide.';
$string['invalidexportvisibility'] = 'Visibilité d’export invalide.';
$string['invalidjsonorlist'] = 'Saisissez un JSON valide ou une liste valide.';
$string['invalidmetadatajson'] = 'JSON des métadonnées invalide.';
$string['invalidshortname'] = 'Nom court invalide.';
$string['invalidsourcecomponent'] = 'Composant source invalide.';
$string['invalidvalidationstate'] = 'État de validation invalide.';
$string['itemcount'] = '{$a} élément(s)';
$string['itemtype:integrity_summary'] = 'Résumé d’intégrité';
$string['itemtype:minutes'] = 'Procès-verbal';
$string['itemtype:public_summary'] = 'Résumé public';
$string['itemvalidated'] = 'Élément validé';
$string['metadatajson'] = 'Métadonnées JSON';
$string['nouserarchiveitems'] = 'Aucun élément de registre utilisateur.';
$string['originarea'] = 'Zone d’origine';
$string['origincomponent'] = 'Composant d’origine';
$string['originid'] = 'ID d’origine';
$string['originrecord'] = 'Enregistrement d’origine';
$string['origintype'] = 'Type d’origine';
$string['privatefeedback'] = 'Rétroaction privée';
$string['proof'] = 'Preuve';
$string['proof_files'] = 'Fichiers de preuve';
$string['proofrecords'] = 'Traces de preuve';
$string['proofs'] = 'Preuves';
$string['proofs:none'] = 'Aucune preuve à afficher.';
$string['provenance:loaded'] = 'Provenance chargée.';
$string['provenance:loadfailed'] = 'Impossible de charger la provenance.';
$string['provenance:loading'] = 'Chargement de la provenance…';
$string['provenancegovernancenotice'] = 'La provenance doit préciser l’origine, l’auteur, les transformations, les limites et les éléments vérifiables.';
$string['provenancemustbeverified'] = 'La provenance doit être vérifiée.';
$string['provenancenotes'] = 'Notes de provenance';
$string['provenancepolicy'] = 'Politique de provenance';
$string['provenancerecordcount'] = 'Nombre de traces de provenance';
$string['provenancerecords'] = 'Traces de provenance';
$string['provenancerecords:none'] = 'Aucune trace de provenance à afficher.';
$string['provenancestatementrequired'] = 'La déclaration de provenance est requise.';
$string['provenancevalidation'] = 'Validation de la provenance';
$string['publicsummary'] = 'Résumé public';
$string['publicsummaryrequired'] = 'Le résumé public est requis.';
$string['readyforexport'] = 'Prêt pour l’export';
$string['recordid'] = 'ID de l’enregistrement';
$string['redactrestrictedexports'] = 'Masquer les exports restreints';
$string['requestexport'] = 'Demander un export';
$string['requestvalidation'] = 'Demander une validation';
$string['required'] = 'Requis';
$string['requiresintegritycase'] = 'Exige un dossier d’intégrité';
$string['requiresrevision'] = 'Exige une révision';
$string['resetarchivespreserved'] = 'Les registres existants ont été conservés pendant la réinitialisation.';
$string['restrictednotes'] = 'Notes restreintes';
$string['restrictednotesrequired'] = 'Les notes restreintes sont requises.';
$string['restrictedvisibletoyou'] = 'Des éléments restreints sont visibles pour vous en raison de vos permissions.';
$string['revisearchiveitem'] = 'Réviser l’élément de registre';
$string['savearchiveitem'] = 'Enregistrer l’élément de registre';
$string['savekristaldraft'] = 'Enregistrer le brouillon de Kristal';
$string['savevalidationdraft'] = 'Enregistrer le brouillon de validation';
$string['scope'] = 'Portée';
$string['shortname'] = 'Nom court';
$string['sourcetitle'] = 'Titre de la source';
$string['sourceverified'] = 'Source vérifiée';
$string['status:pendingreview'] = 'En attente de révision';
$string['submitkristal'] = 'Soumettre le Kristal';
$string['submitvalidation'] = 'Soumettre la validation';
$string['timecreated'] = 'Date de création';
$string['uncertaintynotes'] = 'Notes d’incertitude';
$string['updatepreview'] = 'Mettre à jour l’aperçu';
$string['useroutline'] = 'Résumé des registres utilisateur';
$string['versionnumber'] = 'Numéro de version';
$string['versionx'] = 'Version {$a}';
$string['visibilityandreview'] = 'Visibilité et révision';
$string['visibilityconfirmed'] = 'Visibilité confirmée';
$string['visibilitymustbeconfirmed'] = 'La visibilité doit être confirmée.';
$string['visibilitynotes'] = 'Notes de visibilité';
$string['visibilityreview'] = 'Révision de la visibilité';

// Registraire ajouté depuis l’audit.
$string['archiveaddnotice'] = 'Ajoutez un élément de registre avec une provenance claire, une visibilité appropriée et les preuves nécessaires.';
$string['archiveexport'] = 'Export du registre';
$string['archiveexportqueued'] = 'L’export du registre a été placé en file d’attente.';
$string['archivegovernance'] = 'Gouvernance du registre';
$string['archiveitem:loaded'] = 'Élément de registre chargé.';
$string['archiveitem:loadfailed'] = 'Impossible de charger l’élément de registre.';
$string['archiveitem:loading'] = 'Chargement de l’élément de registre…';
$string['archiveitemactions'] = 'Actions sur l’élément de registre';
$string['archiveitembody'] = 'Corps de l’élément de registre';
$string['archiveitemcontent'] = 'Contenu de l’élément de registre';
$string['archiveitemfiles'] = 'Fichiers de l’élément de registre';
$string['archiveitemgovernancenotice'] = 'La modification d’un élément de registre doit conserver la provenance, respecter la visibilité et préserver l’historique de révision.';
$string['archiveitemidentity'] = 'Identité de l’élément de registre';
$string['archiveitempolicy'] = 'Politique des éléments de registre';
$string['archiveitemrequirescontent'] = 'L’élément de registre doit contenir un contenu, un résumé ou un fichier.';
$string['archiveitems:none'] = 'Aucun élément de registre à afficher.';
$string['archiveitemtitle'] = 'Titre de l’élément de registre';
$string['archiveitemtype'] = 'Type d’élément de registre';
$string['archivememorynotice'] = 'Ce registre conserve une mémoire vérifiable des éléments, preuves, révisions et décisions associés.';
$string['archivemissingidentifiers'] = 'Identifiants de registre manquants.';
$string['archivereason'] = 'Raison de classement';
$string['archivescope'] = 'Portée du registre';
$string['archivescopefield'] = 'Champ de portée du registre';
$string['archivesource'] = 'Source du registre';
$string['archivestatus'] = 'Statut du registre';
$string['archivetype'] = 'Type de registre';
$string['archivetype:assembly_memory'] = 'Mémoire d’assemblée';
$string['archivetype:challenge_output'] = 'Production de défi';
$string['archivetype:course_memory'] = 'Mémoire de cours';
$string['archivetype:integrity_memory'] = 'Mémoire d’intégrité';
$string['archivetype:kristal_library'] = 'Bibliothèque de Kristals';
$string['archivetype:portfolio_archive'] = 'Registre de portfolio';
$string['archivetype:proof_repository'] = 'Dépôt de preuves';
$string['archivevalidation'] = 'Validation du registre';

// Kristals ajoutés depuis l’audit.
$string['kristalalignment'] = 'Alignement du Kristal';
$string['kristalbody'] = 'Corps du Kristal';
$string['kristalbodyrequired'] = 'Le corps du Kristal est requis.';
$string['kristalcontent'] = 'Contenu du Kristal';
$string['kristalerror'] = 'Erreur de Kristal';
$string['kristalgovernancenotice'] = 'Un Kristal doit déclarer sa provenance, ses limites, son usage d’IA et son niveau de visibilité.';
$string['kristalidentity'] = 'Identité du Kristal';
$string['kristalmissingcontent'] = 'Le contenu du Kristal est manquant.';
$string['kristalmissingtitle'] = 'Le titre du Kristal est manquant.';
$string['kristalrefreshed'] = 'Kristal actualisé.';
$string['kristalrefreshfailed'] = 'Impossible d’actualiser le Kristal.';
$string['kristalrefreshing'] = 'Actualisation du Kristal…';
$string['kristals:none'] = 'Aucun Kristal à afficher.';
$string['kristalsaved'] = 'Kristal enregistré.';
$string['kristalsavefailed'] = 'Impossible d’enregistrer le Kristal.';
$string['kristalsaving'] = 'Enregistrement du Kristal…';
$string['kristalshortname'] = 'Nom court du Kristal';
$string['kristalsubmitfailed'] = 'Impossible de soumettre le Kristal.';
$string['kristalsubmitted'] = 'Kristal soumis.';
$string['kristalsubmitting'] = 'Soumission du Kristal…';
$string['kristalsummary'] = 'Résumé du Kristal';
$string['kristaltype:canonlink'] = 'Lien canonique';
$string['kristaltype:concept'] = 'Concept';
$string['kristaltype:decisionmemory'] = 'Mémoire de décision';
$string['kristaltype:definition'] = 'Définition';
$string['kristaltype:principle'] = 'Principe';
$string['kristaltype:proofsynthesis'] = 'Synthèse de preuves';
$string['kristaltype:synthesis'] = 'Synthèse';

// Validation et révision ajoutées depuis l’audit.
$string['retentionnotes'] = 'Notes de conservation';
$string['retentionpolicy'] = 'Politique de conservation';
$string['retentionpolicy:course_lifetime'] = 'Durée de vie du cours';
$string['retentionpolicy:institutional_memory'] = 'Mémoire institutionnelle';
$string['retentionpolicy:program_lifetime'] = 'Durée de vie du programme';
$string['retentionpolicy:restricted_integrity'] = 'Conservation d’intégrité restreinte';
$string['revisionandmemory'] = 'Révision et mémoire';
$string['revisionandretention'] = 'Révision et conservation';
$string['revisionhistory'] = 'Historique des révisions';
$string['revisioninstructions'] = 'Instructions de révision';
$string['revisioninstructionsrequired'] = 'Les instructions de révision sont requises.';
$string['revisionpolicy'] = 'Politique de révision';
$string['revisionpolicy:none'] = 'Aucune révision automatique';
$string['revisionpolicy:version_every_edit'] = 'Versionner chaque modification';
$string['revisionpolicy:version_on_change'] = 'Versionner lors d’un changement significatif';
$string['revisionpolicy:version_on_validation'] = 'Versionner lors de la validation';
$string['validatearchiveitems'] = 'Valider les éléments de registre';
$string['validateditemneedsreviewstate'] = 'Un élément validé doit utiliser un état de validation de révision.';
$string['validationcriteria'] = 'Critères de validation';
$string['validationgovernancenotice'] = 'La validation doit rester humaine, traçable et appuyée par une provenance vérifiable.';
$string['validationgrade'] = 'Note de validation';
$string['validationgrademustbeinrange'] = 'La note de validation doit être comprise dans l’intervalle autorisé.';
$string['validationrequested'] = 'Validation demandée.';
$string['validationstatement'] = 'Déclaration de validation';
$string['validationstatementrequired'] = 'La déclaration de validation est requise.';
$string['validationworkflow'] = 'Flux de validation';
$string['validationworkflow:archivist_review'] = 'Révision par responsable du registre';
$string['validationworkflow:human_review'] = 'Révision humaine';
$string['validationworkflow:integrity_review'] = 'Révision d’intégrité';
$string['validationworkflow:none'] = 'Aucun flux de validation';

// Exports ajoutés depuis l’audit.
$string['export:failed'] = 'L’export a échoué.';
$string['export:noitems:body'] = 'Aucun élément ne correspond aux critères d’export sélectionnés.';
$string['export:noitems:title'] = 'Aucun élément à exporter';
$string['export:previewfailed'] = 'Impossible de charger l’aperçu de l’export.';
$string['export:previewloaded'] = 'Aperçu de l’export chargé.';
$string['export:previewloading'] = 'Chargement de l’aperçu de l’export…';
$string['export:started'] = 'Export démarré.';
$string['export:starting'] = 'Démarrage de l’export…';
$string['exportarchiveitem'] = 'Exporter l’élément de registre';
$string['exportauditnote'] = 'Note d’audit de l’export';
$string['exportcancelfailed'] = 'Impossible d’annuler l’export.';
$string['exportcancelled'] = 'Export annulé.';
$string['exportconfirmpolicy'] = 'Je confirme que cet export respecte la politique de visibilité, de provenance et de protection des données.';
$string['exportconfirmpolicyrequired'] = 'Vous devez confirmer la politique d’export.';
$string['exportdescription'] = 'Description de l’export';
$string['exporterror'] = 'Erreur d’export';
$string['exporterror:missingarchive'] = 'Registre manquant pour la génération de l’export.';
$string['exportformat:html'] = 'HTML';
$string['exportformat:mbz_manifest'] = 'Manifeste MBZ';
$string['exportgovernance'] = 'Gouvernance de l’export';
$string['exportgovernancenotice'] = 'Les exports doivent respecter la visibilité, les restrictions d’intégrité, la redaction et la finalité déclarée.';
$string['exportincludefiles'] = 'Inclure les fichiers';
$string['exportincludehashes'] = 'Inclure les empreintes';
$string['exportincludeintegritysummary'] = 'Inclure le résumé d’intégrité';
$string['exportincludekristals'] = 'Inclure les Kristals';
$string['exportincludemetadata'] = 'Inclure les métadonnées';
$string['exportincludeprivatefields'] = 'Inclure les champs privés';
$string['exportincludeversions'] = 'Inclure les versions';
$string['exportitemids'] = 'Identifiants des éléments à exporter';
$string['exportitemidsrequired'] = 'Sélectionnez au moins un élément à exporter.';
$string['exportmissingidentifiers'] = 'Identifiants d’export manquants.';
$string['exportmode'] = 'Mode d’export';
$string['exportmode:immediate'] = 'Immédiat';
$string['exportmode:queued'] = 'En file d’attente';
$string['exportnotice'] = 'Avis d’export';
$string['exportnotice_desc'] = 'Message affiché aux utilisateurs avant la génération d’un export.';
$string['exportoptions'] = 'Options d’export';
$string['exportpackagename'] = 'Nom du paquet d’export';
$string['exportpolicy'] = 'Politique d’export';
$string['exportpolicy:full_with_revisions'] = 'Export complet avec révisions';
$string['exportpolicy:none'] = 'Aucun export';
$string['exportpolicy:public_only'] = 'Éléments publics seulement';
$string['exportpolicy:restricted_redacted'] = 'Restreint avec données masquées';
$string['exportpolicy:validated_only'] = 'Éléments validés seulement';
$string['exportpollingstopped'] = 'Le suivi de l’export a été interrompu.';
$string['exportpreparing'] = 'Préparation de l’export…';
$string['exportpreview'] = 'Aperçu de l’export';
$string['exportprivacy'] = 'Confidentialité de l’export';
$string['exportprovenance'] = 'Provenance de l’export';
$string['exportready'] = 'Export prêt.';
$string['exportreasonrequired'] = 'Une raison d’export est requise.';
$string['exportredactpersonaldata'] = 'Masquer les données personnelles';
$string['exportrefreshed'] = 'Export actualisé.';
$string['exportrefreshfailed'] = 'Impossible d’actualiser l’export.';
$string['exportrefreshing'] = 'Actualisation de l’export…';
$string['exportrestrictednotallowed'] = 'Les éléments restreints ne peuvent pas être inclus dans cet export.';
$string['exports'] = 'Exports';
$string['exports:none'] = 'Aucun export à afficher.';
$string['exportscope:portfolio'] = 'Portfolio';
$string['exportscope:publicitems'] = 'Éléments publics';
$string['exportscope:restrictedintegrity'] = 'Intégrité restreinte';
$string['exportscope:selecteditems'] = 'Éléments sélectionnés';
$string['exportscope:validateditems'] = 'Éléments validés';
$string['exportstatusfilter'] = 'Filtre de statut d’export';
$string['exportsummary'] = 'Résumé de l’export';
$string['exporttimefrom'] = 'Exporter à partir du';
$string['exporttimeto'] = 'Exporter jusqu’au';
$string['exporttimetomustbeafterfrom'] = 'La date de fin doit être postérieure à la date de début.';
$string['exporttypefilter'] = 'Filtre de type d’export';
$string['exportunredactednotallowed'] = 'L’export non masqué n’est pas autorisé pour ces éléments.';

// Paramètres ajoutés depuis l’audit.
$string['settings:ai'] = 'IA';
$string['settings:ai_desc'] = 'Configurer les règles d’assistance IA, de journalisation et d’incertitude pour les registres.';
$string['settings:allowaiassistance'] = 'Autoriser l’assistance IA';
$string['settings:allowaiassistance_desc'] = 'Autoriser la déclaration et l’utilisation encadrée d’une assistance IA dans les éléments de registre et les Kristals.';
$string['settings:allowaivalidation'] = 'Autoriser l’aide IA à la validation';
$string['settings:allowaivalidation_desc'] = 'Autoriser l’IA à soutenir la validation sans remplacer la décision humaine.';
$string['settings:allowpublicitems'] = 'Autoriser les éléments publics';
$string['settings:allowpublicitems_desc'] = 'Autoriser les éléments de registre à devenir publics après validation et vérification de la visibilité.';
$string['settings:blockrestrictedexports'] = 'Bloquer les exports restreints';
$string['settings:blockrestrictedexports_desc'] = 'Empêcher les exports contenant des éléments restreints sauf autorisation explicite.';
$string['settings:defaultexportformat'] = 'Format d’export par défaut';
$string['settings:defaultexportformat_desc'] = 'Format utilisé par défaut pour les nouveaux paquets d’export.';
$string['settings:defaultprovenance'] = 'Provenance par défaut';
$string['settings:defaultprovenance_desc'] = 'Provenance appliquée par défaut aux nouveaux éléments lorsque l’utilisateur n’en indique pas une.';
$string['settings:defaultvalidationstate'] = 'État de validation par défaut';
$string['settings:defaultvalidationstate_desc'] = 'État de validation initial appliqué aux nouveaux éléments de registre.';
$string['settings:enabled'] = 'Activer les Registres UCKK';
$string['settings:enabled_desc'] = 'Activer les fonctionnalités du module d’activité Registraire UCKK.';
$string['settings:enablerevisions'] = 'Activer les révisions';
$string['settings:enablerevisions_desc'] = 'Conserver un historique de révision pour les éléments de registre.';
$string['settings:enablevalidation'] = 'Activer la validation';
$string['settings:enablevalidation_desc'] = 'Permettre la validation, le rejet et l’invalidation des éléments de registre.';
$string['settings:export'] = 'Export';
$string['settings:export_desc'] = 'Configurer les formats, restrictions et politiques d’export des registres.';
$string['settings:generateexports'] = 'Générer les exports';
$string['settings:generateexports_desc'] = 'Autoriser la tâche planifiée à générer les exports en file d’attente.';
$string['settings:includefilesinexports'] = 'Inclure les fichiers dans les exports';
$string['settings:includefilesinexports_desc'] = 'Inclure les fichiers attachés lorsque la politique d’export l’autorise.';
$string['settings:itempolicy'] = 'Politique des éléments';
$string['settings:itempolicy_desc'] = 'Configurer les règles de création, visibilité, provenance et protection des éléments de registre.';
$string['settings:kristal'] = 'Kristals';
$string['settings:kristal_desc'] = 'Configurer la création, la validation et le nombre maximal de Kristals.';
$string['settings:kristalsrequirevalidation'] = 'Exiger la validation des Kristals';
$string['settings:kristalsrequirevalidation_desc'] = 'Exiger une validation humaine avant qu’un Kristal soit considéré comme vérifié.';
$string['settings:lockvalidateditems'] = 'Verrouiller les éléments validés';
$string['settings:lockvalidateditems_desc'] = 'Empêcher la modification directe des éléments validés sans révision ou changement d’état.';
$string['settings:logaiuse'] = 'Journaliser l’usage de l’IA';
$string['settings:logaiuse_desc'] = 'Conserver les traces déclarées d’assistance IA, de prompts, de réponses ou de métadonnées selon la politique du registre.';
$string['settings:maxkristalitems'] = 'Nombre maximal de Kristals';
$string['settings:maxkristalitems_desc'] = 'Nombre maximal de Kristals pouvant être associés à un registre ou à un élément.';
$string['settings:pausevalidationonintegritycase'] = 'Suspendre la validation en cas de dossier d’intégrité';
$string['settings:pausevalidationonintegritycase_desc'] = 'Empêcher la validation finale lorsqu’un dossier d’intégrité actif concerne l’élément.';
$string['settings:protectrestricteditems'] = 'Protéger les éléments restreints';
$string['settings:protectrestricteditems_desc'] = 'Appliquer des contrôles supplémentaires aux éléments marqués comme restreints ou restreints à l’intégrité.';
$string['settings:requireaiuncertaintylabel'] = 'Exiger une mention d’incertitude IA';
$string['settings:requireaiuncertaintylabel_desc'] = 'Exiger une mention des limites et incertitudes lorsque l’IA contribue au contenu.';
$string['settings:requirechangereason'] = 'Exiger une raison de changement';
$string['settings:requirechangereason_desc'] = 'Exiger une justification lors d’une révision, invalidation ou modification d’un élément validé.';
$string['settings:requirecontext'] = 'Exiger le contexte';
$string['settings:requirecontext_desc'] = 'Exiger que les éléments de registre décrivent leur contexte d’origine.';
$string['settings:requirehumanvalidation'] = 'Exiger une validation humaine';
$string['settings:requirehumanvalidation_desc'] = 'Exiger une décision humaine pour valider, rejeter ou invalider un élément.';
$string['settings:requirevisibility'] = 'Exiger la visibilité';
$string['settings:requirevisibility_desc'] = 'Exiger qu’un niveau de visibilité explicite soit défini pour chaque élément.';
$string['settings:taskbatchsize'] = 'Taille des lots de tâche';
$string['settings:taskbatchsize_desc'] = 'Nombre maximal d’éléments traités par lot dans les tâches planifiées de registre.';
$string['settings:tasks'] = 'Tâches planifiées';
$string['settings:tasks_desc'] = 'Configurer les tâches planifiées de validation, d’export et de nettoyage.';
$string['settings:validatependingitems'] = 'Valider les éléments en attente';
$string['settings:validatependingitems_desc'] = 'Autoriser la tâche planifiée à examiner les éléments en attente de validation.';
$string['settings:validation'] = 'Validation';
$string['settings:validation_desc'] = 'Configurer les règles de validation, révision, contestation et verrouillage.';

// Badges et avis ajoutés depuis l’audit.
$string['badge:aiassisted'] = 'Assisté par IA';
$string['badge:contested'] = 'Contesté';
$string['badge:invalidated'] = 'Invalidé';
$string['badge:restricted'] = 'Restreint';
$string['badge:validated'] = 'Validé';
$string['notice:aiassisted'] = 'Cet élément indique une assistance par IA.';
$string['notice:archiveitem'] = 'Cet élément fait partie de le Registraire UCKK.';
$string['notice:restricted'] = 'Cet élément contient des données restreintes.';

// Tâches et calendrier ajoutés depuis l’audit.
$string['calendarevent:closes'] = '{$a} se ferme';
$string['calendarevent:opens'] = '{$a} s’ouvre';
$string['task:validation_correction_reason'] = 'Correction requise par la tâche de validation.';
$string['task:validation_ready_reason'] = 'Élément prêt pour la validation automatique programmée.';
$string['task_generate_archive_exports'] = 'Générer les exports du registre';

// Confidentialité ajoutée depuis l’audit.
$string['privacy:deleted'] = 'Les données de registre supprimées ne sont plus disponibles dans cette activité.';

// -----------------------------------------------------------------------------
// Médias, avis de contenu, œuvres externes et intégrations Moodle ajoutés.
// -----------------------------------------------------------------------------

$string['actor'] = 'Acteur';
$string['addcollection'] = 'Ajouter une collection';
$string['addcontentmarker'] = 'Ajouter un marqueur de contenu';
$string['addmedia'] = 'Ajouter un média';
$string['addmediarelation'] = 'Ajouter une relation de média';
$string['addmediaversion'] = 'Ajouter une version de média';
$string['addtocollection'] = 'Ajouter à la collection';
$string['advisoryhintrequired'] = 'Une indication d’avis de contenu est requise.';
$string['advisoryseverity'] = 'Gravité de l’avis';
$string['advisoryseverity:moderate'] = 'Modéré';
$string['advisoryseverity:notice'] = 'Avis';
$string['advisoryseverity:restricted'] = 'Restreint';
$string['advisoryseverity:strong'] = 'Fort';
$string['aiassistancedisclosed'] = 'Assistance IA déclarée';
$string['aiprovencenotice'] = 'L’assistance IA doit rester traçable, déclarée et vérifiable.';
$string['allstatuses'] = 'Tous les statuts';
$string['allvalidationstates'] = 'Tous les états de validation';
$string['archived'] = 'Classé';
$string['archivefilters'] = 'Filtres de registre';
$string['archivestats'] = 'Statistiques de registre';
$string['archivesummary'] = 'Résumé du registre';
$string['attentionrequired'] = 'Attention requise';
$string['audience'] = 'Public';
$string['audience:general'] = 'Général';
$string['audience:guided'] = 'Accompagné';
$string['audience:mature'] = 'Adulte';
$string['audience:restricted'] = 'Restreint';
$string['audience:restricted_cultural'] = 'Restreint culturel';
$string['audience:restricted_integrity'] = 'Restreint à l’intégrité';
$string['audience:staff_only'] = 'Personnel seulement';
$string['audiencesuitability'] = 'Adéquation au public';
$string['audio'] = 'Audio';
$string['author'] = 'Auteur';
$string['by'] = 'Par';
$string['citation'] = 'Citation';
$string['clearfilters'] = 'Effacer les filtres';
$string['collection'] = 'Collection';
$string['collections'] = 'Collections';
$string['confirmdeletemedia'] = 'Supprimer ce média ?';
$string['contentadvisories'] = 'Avis de contenu';
$string['contentadvisory'] = 'Avis de contenu';
$string['contentadvisory:title'] = 'Avis de contenu';
$string['contentadvisoryhints'] = 'Indications d’avis de contenu';
$string['contentadvisoryseverity'] = 'Gravité de l’avis de contenu';
$string['contenthash'] = 'Empreinte du contenu';
$string['contentmarkerrequired'] = 'Un marqueur de contenu est requis.';
$string['contentmarkers'] = 'Marqueurs de contenu';
$string['contentreview'] = 'Revue de contenu';
$string['contentreview:culturalprotocol_help'] = 'Indiquez si cette revue implique un protocole culturel ou une restriction culturelle.';
$string['contentreview:restricted_help'] = 'Indiquez si ce contenu doit rester restreint.';
$string['contentreviewfiles'] = 'Fichiers de revue de contenu';
$string['contentreviewnote'] = 'Note de revue de contenu';
$string['contentreviewrationale'] = 'Justification de la revue';
$string['contentreviewrationalerequired'] = 'La justification de la revue est requise.';
$string['contentreviewrestrictedrationalerequired'] = 'Une justification est requise pour le contenu restreint.';
$string['contentreviewstate'] = 'État de revue de contenu';
$string['contenttag:active'] = 'Étiquette active';
$string['contenttag:active_desc'] = 'Cette étiquette peut être utilisée pour de nouveaux marqueurs de contenu.';
$string['contenttag:advisory'] = 'Avis';
$string['contenttag:category'] = 'Catégorie';
$string['contenttag:defaultaudience'] = 'Public par défaut';
$string['contenttag:description'] = 'Description';
$string['contenttag:error:invalidaudience'] = 'Public invalide.';
$string['contenttag:error:invalidcategory'] = 'Catégorie invalide.';
$string['contenttag:error:invalidmetadata'] = 'Métadonnées invalides.';
$string['contenttag:error:invalidreviewstate'] = 'État de revue invalide.';
$string['contenttag:error:invalidseverity'] = 'Gravité invalide.';
$string['contenttag:error:invalidtagkey'] = 'Clé d’étiquette invalide.';
$string['contenttag:identity'] = 'Identité de l’étiquette';
$string['contenttag:iscultural'] = 'Étiquette culturelle';
$string['contenttag:iscultural_desc'] = 'Cette étiquette indique un contenu culturellement sensible.';
$string['contenttag:label'] = 'Libellé';
$string['contenttag:metadata'] = 'Métadonnées';
$string['contenttag:metadatajson'] = 'Métadonnées JSON';
$string['contenttag:restrictsdefault'] = 'Restreint par défaut';
$string['contenttag:restrictsdefault_desc'] = 'Les marqueurs créés avec cette étiquette sont restreints par défaut.';
$string['contenttag:review'] = 'Revue';
$string['contenttag:reviewstate'] = 'État de revue';
$string['contenttag:severity'] = 'Gravité';
$string['contenttag:sortorder'] = 'Ordre de tri';
$string['contenttag:tag'] = 'Étiquette';
$string['contenttag:tagkey'] = 'Clé d’étiquette';
$string['contenttag:tagset'] = 'Ensemble d’étiquettes';
$string['contentwarnings'] = 'Avertissements de contenu';
$string['culturallyrestricted'] = 'Culturellement restreint';
$string['culturalprotocol'] = 'Protocole culturel';
$string['culturalprotocolnote'] = 'Note de protocole culturel';
$string['culturalprotocolnoterequired'] = 'Une note de protocole culturel est requise.';
$string['culturalprotocolrequired'] = 'Un protocole culturel est requis.';
$string['culturalprotocols'] = 'Protocoles culturels';
$string['delete'] = 'Supprimer';
$string['deleted'] = 'Supprimé';
$string['document'] = 'Document';
$string['event:archiveviewed'] = 'Registre consulté';
$string['event:contentmarkercreated'] = 'Marqueur de contenu créé';
$string['event:contentmarkerreviewed'] = 'Marqueur de contenu revu';
$string['event:externalworkcreated'] = 'Œuvre externe créée';
$string['event:mediacreated'] = 'Média créé';
$string['event:mediaupdated'] = 'Média mis à jour';
$string['event:mediaversioncreated'] = 'Version de média créée';
$string['eventcontentmarkercreated'] = 'Marqueur de contenu créé';
$string['eventcontentmarkerreviewed'] = 'Marqueur de contenu revu';
$string['eventexternalworkcreated'] = 'Œuvre externe créée';
$string['eventmediacollectioncreated'] = 'Collection de médias créée';
$string['eventmediacreated'] = 'Média créé';
$string['eventmediaexported'] = 'Média exporté';
$string['eventmediaupdated'] = 'Média mis à jour';
$string['eventmediaversioncreated'] = 'Version de média créée';
$string['exportmedia'] = 'Exporter le média';
$string['externalreference'] = 'Référence externe';
$string['externalurl'] = 'URL externe';
$string['openexternal'] = 'Ouvrir la référence externe';
$string['openexternal_help'] = 'Ouvre l’URL source externe dans un nouvel onglet. La fiche média reste gouvernée par les métadonnées UCKK, les droits, la visibilité, les avis de contenu et les protocoles culturels.';
$string['mediaexternalreference'] = 'Référence externe';
$string['mediaexternalurl'] = 'URL externe';
$string['mediaopenexternal'] = 'Ouvrir la référence externe';
$string['externalwork'] = 'Œuvre externe';
$string['externalworkcitation'] = 'Citation de l’œuvre externe';
$string['externalworkcreator'] = 'Créateur de l’œuvre externe';
$string['externalworkculturalprotocolnote'] = 'Note de protocole culturel de l’œuvre externe';
$string['externalworkdescription'] = 'Description de l’œuvre externe';
$string['externalworkgovernance'] = 'Gouvernance des œuvres externes';
$string['externalworkid'] = 'ID de l’œuvre externe';
$string['externalworkidentifier'] = 'Identifiant de l’œuvre externe';
$string['externalworkidentifiertype'] = 'Type d’identifiant de l’œuvre externe';
$string['externalworkidentity'] = 'Identité de l’œuvre externe';
$string['externalworklanguage'] = 'Langue de l’œuvre externe';
$string['externalworklicensekey'] = 'Clé de licence de l’œuvre externe';
$string['externalworklicenserequired'] = 'Une licence ou une justification des droits est requise.';
$string['externalworknote'] = 'Note sur l’œuvre externe';
$string['externalworkpublicationyear'] = 'Année de publication';
$string['externalworkpublisher'] = 'Éditeur ou diffuseur';
$string['externalworkreference'] = 'Référence d’œuvre externe';
$string['externalworkreferencerequired'] = 'Une référence d’œuvre externe est requise.';
$string['externalworkrestrictionnoterequired'] = 'Une note de restriction est requise pour cette œuvre externe.';
$string['externalworkrights'] = 'Droits de l’œuvre externe';
$string['externalworkrightsstatement'] = 'Déclaration de droits';
$string['externalworkrightsstatementrequired'] = 'Une déclaration de droits est requise.';
$string['externalworkrightsstatus'] = 'Statut des droits';
$string['externalworksource'] = 'Source de l’œuvre externe';
$string['externalworksourcenote'] = 'Note de source';
$string['externalworksourceurl'] = 'URL source';
$string['externalworksubtitle'] = 'Sous-titre';
$string['externalworkteachingandprotocol'] = 'Enseignement et protocole';
$string['externalworkteachingnote'] = 'Note pédagogique';
$string['externalworktitle'] = 'Titre de l’œuvre externe';
$string['externalworktype'] = 'Type d’œuvre externe';
$string['externalworktype:article'] = 'Article';
$string['externalworktype:book'] = 'Livre';
$string['externalworktype:external_image'] = 'Image externe';
$string['externalworktype:external_video'] = 'Vidéo externe';
$string['externalworktype:film'] = 'Film';
$string['externalworktype:other'] = 'Autre';
$string['externalworktype:podcast'] = 'Podcast';
$string['externalworktype:public_archive_item'] = 'Élément de registre public';
$string['externalworktype:third_party_pdf'] = 'PDF tiers';
$string['externalworktype:website'] = 'Site web';
$string['externalworkyear'] = 'Année de l’œuvre externe';
$string['filearea'] = 'Zone de fichiers';
$string['filearea:media_attachment'] = 'Pièces jointes de média';
$string['filearea:media_caption'] = 'Sous-titres de média';
$string['filearea:media_derivative'] = 'Dérivés de média';
$string['filearea:media_original'] = 'Fichiers média originaux';
$string['filearea:media_preview'] = 'Aperçus de média';
$string['filearea:media_thumbnail'] = 'Vignettes de média';
$string['filearea:media_transcript'] = 'Transcriptions de média';
$string['filename'] = 'Nom de fichier';
$string['filesize'] = 'Taille du fichier';
$string['identifier'] = 'Identifiant';
$string['identifiertype:accession_number'] = 'Numéro d’acquisition';
$string['identifiertype:archive_identifier'] = 'Identifiant de registre';
$string['identifiertype:catalogue_number'] = 'Numéro de catalogue';
$string['identifiertype:doi'] = 'DOI';
$string['identifiertype:isbn'] = 'ISBN';
$string['identifiertype:issn'] = 'ISSN';
$string['identifiertype:local_identifier'] = 'Identifiant local';
$string['identifiertype:other'] = 'Autre';
$string['identifiertype:uri'] = 'URI';
$string['identifiertype:url'] = 'URL';
$string['image'] = 'Image';
$string['integrity'] = 'Intégrité';
$string['integrityrestricted'] = 'Restreint à l’intégrité';
$string['integrityreviewrequired'] = 'Une revue d’intégrité est requise.';
$string['internalnote'] = 'Note interne';
$string['invalidaudiencesuitability'] = 'Adéquation au public invalide.';
$string['invalidexternalworkyear'] = 'Année de l’œuvre externe invalide.';
$string['invalidjson'] = 'JSON invalide.';
$string['invalidmetadata'] = 'Métadonnées invalides.';
$string['invalidseverity'] = 'Gravité invalide.';
$string['invalidstate'] = 'État invalide.';
$string['invalidtaglist'] = 'Liste d’étiquettes invalide.';
$string['itemtype_challenge_result'] = 'Résultat de défi';
$string['itemtype_course_work'] = 'Travail de cours';
$string['itemtype_decision'] = 'Décision';
$string['itemtype_integrity_summary'] = 'Résumé d’intégrité';
$string['itemtype_kristal'] = 'Kristal';
$string['itemtype_minutes'] = 'Procès-verbal';
$string['itemtype_portfolio_item'] = 'Élément de portfolio';
$string['itemtype_proof'] = 'Preuve';
$string['itemtype_public_summary'] = 'Résumé public';
$string['makecurrent'] = 'Rendre actuelle';
$string['manageadvisories'] = 'Gérer les avis';
$string['media'] = 'Média';
$string['media:alttext'] = 'Texte alternatif';
$string['media:alttext_help'] = 'Texte alternatif décrivant le média pour l’accessibilité.';
$string['media:audiencesuitability'] = 'Adéquation au public';
$string['media:caption'] = 'Légende';
$string['media:license'] = 'Licence du média';
$string['media:rightsnote'] = 'Note sur les droits';
$string['media:source'] = 'Source du média';
$string['media:type'] = 'Type de média';
$string['mediaadvisoryhint'] = 'Indication d’avis de contenu pour le média';
$string['mediaalttext'] = 'Texte alternatif du média';
$string['mediacitation'] = 'Citation du média';
$string['mediacollection:noitems'] = 'Cette collection ne contient aucun média.';
$string['mediacollectionhint'] = 'Mediacollectionhint';
$string['mediacollections'] = 'Collections de médias';
$string['mediacreator'] = 'Mediacreator';
$string['mediadatecreated'] = 'Mediadatecreated';
$string['mediadescription'] = 'Description du média';
$string['mediafile'] = 'Fichier média';
$string['mediafilearea'] = 'Mediafilearea';
$string['mediafiles'] = 'Fichiers média';
$string['mediagovernance'] = 'Gouvernance des médias';
$string['mediahascontentadvisory'] = 'Mediahascontentadvisory';
$string['mediaid'] = 'ID du média';
$string['mediaidentity'] = 'Identité du média';
$string['mediaitems'] = 'Mediaitems';
$string['medialanguage'] = 'Medialanguage';
$string['medialibrary'] = 'Médiathèque';
$string['medialibraryerror'] = 'Medialibraryerror';
$string['medialicense'] = 'Medialicense';
$string['mediarelation'] = 'Relation de média';
$string['mediarelationfromid'] = 'Mediarelationfromid';
$string['mediarelationfromtype'] = 'Mediarelationfromtype';
$string['mediarelationidentity'] = 'Mediarelationidentity';
$string['mediarelationinvalidtargettype'] = 'Mediarelationinvalidtargettype';
$string['mediarelationnote'] = 'Mediarelationnote';
$string['mediarelationobject:archive_item'] = 'Élément de registre';
$string['mediarelationobject:content_marker'] = 'Contenu marqueur';
$string['mediarelationobject:external_work'] = 'Externe œuvre';
$string['mediarelationobject:kristal'] = 'Kristal';
$string['mediarelationobject:media'] = 'Média';
$string['mediarelationobject:media_collection'] = 'Média collection';
$string['mediarelationobject:media_collection_item'] = 'Média collection item';
$string['mediarelationobject:media_version'] = 'Média version';
$string['mediarelationobject:proof'] = 'Preuve';
$string['mediarelationrequiresmediaobjects'] = 'Mediarelationrequiresmediaobjects';
$string['mediarelationrequiresmediaobjectsource'] = 'Mediarelationrequiresmediaobjectsource';
$string['mediarelations'] = 'Relations de média';
$string['mediarelationselfnotallowed'] = 'Mediarelationselfnotallowed';
$string['mediarelationtoid'] = 'Mediarelationtoid';
$string['mediarelationtotype'] = 'Mediarelationtotype';
$string['mediarelationtype'] = 'Mediarelationtype';
$string['mediarelationtype:belongs_to_collection'] = 'Belongs vers collection';
$string['mediarelationtype:belongs_to_item'] = 'Belongs vers item';
$string['mediarelationtype:belongs_to_kristal'] = 'Belongs vers kristal';
$string['mediarelationtype:contains_content_marker'] = 'Contains contenu marqueur';
$string['mediarelationtype:duplicates'] = 'Duplicates';
$string['mediarelationtype:is_derivative_of'] = 'Is dérivé of';
$string['mediarelationtype:is_excerpt_of'] = 'Is excerpt of';
$string['mediarelationtype:is_proof_for'] = 'Is preuve for';
$string['mediarelationtype:is_source_for'] = 'Is source for';
$string['mediarelationtype:is_translation_of'] = 'Is translation of';
$string['mediarelationtype:references'] = 'References';
$string['mediarelationtype:references_external_work'] = 'References externe œuvre';
$string['mediarelationtype:replaces'] = 'Replaces';
$string['mediarightsnote'] = 'Mediarightsnote';
$string['mediasource'] = 'Source du média';
$string['mediasource:external_reference_only'] = 'Externe reference seulement';
$string['mediasource:fair_use_reference'] = 'Fair use reference';
$string['mediasource:imported'] = 'Imported';
$string['mediasource:licensed_external'] = 'Licensed externe';
$string['mediasource:produced_by_uckk'] = 'Produced par uckk';
$string['mediasource:public_domain'] = 'Public domain';
$string['mediasource:restricted_reference'] = 'Restreint reference';
$string['mediasource:submitted_to_uckk'] = 'Submitted vers uckk';
$string['mediasourceownership'] = 'Mediasourceownership';
$string['mediasourcetype'] = 'Mediasourcetype';
$string['mediasourceurl'] = 'Mediasourceurl';
$string['mediastatus'] = 'Mediastatus';
$string['mediastatus_active'] = 'Actif';
$string['mediastatus_archived'] = 'Classé';
$string['mediastatus_deleted_soft'] = 'Supprimé logiquement';
$string['mediastatus_draft'] = 'Brouillon';
$string['mediastatus_restricted'] = 'Restreint';
$string['mediatags'] = 'Étiquettes média';
$string['mediatitle'] = 'Titre du média';
$string['mediatranscriptsummary'] = 'Mediatranscriptsummary';
$string['mediatype'] = 'Mediatype';
$string['mediatype:attachment'] = 'Pièce jointe';
$string['mediatype:audio'] = 'Audio';
$string['mediatype:caption'] = 'Sous titre';
$string['mediatype:derivative'] = 'Dérivé';
$string['mediatype:document'] = 'Document';
$string['mediatype:external'] = 'Externe';
$string['mediatype:image'] = 'Image';
$string['mediatype:other'] = 'Other';
$string['mediatype:pdf'] = 'Pdf';
$string['mediatype:preview'] = 'Aperçu';
$string['mediatype:thumbnail'] = 'Vignette';
$string['mediatype:transcript'] = 'Transcription';
$string['mediatype:video'] = 'Video';
$string['mediatype_audio'] = 'Audio';
$string['mediatype_document'] = 'Document';
$string['mediatype_image'] = 'Image';
$string['mediatype_link'] = 'Lien';
$string['mediatype_other'] = 'Autre';
$string['mediatype_video'] = 'Vidéo';
$string['mediaupload:access'] = 'Access';
$string['mediaupload:advisorylater'] = 'Advisorylater';
$string['mediaupload:description'] = 'Description';
$string['mediaupload:dropfile'] = 'Dropfile';
$string['mediaupload:file'] = 'Fichier';
$string['mediaupload:isversionupload'] = 'Isversionupload';
$string['mediaupload:metadata'] = 'Métadonnées du média';
$string['mediaupload:needsadvisory'] = 'Needsadvisory';
$string['mediaupload:newversion'] = 'Newversion';
$string['mediaupload:nopermission'] = 'Nopermission';
$string['mediaupload:rights'] = 'Droits';
$string['mediaupload:save'] = 'Enregistrer le média';
$string['mediaupload:saveversion'] = 'Enregistrer une version du média';
$string['mediaupload:title'] = 'Téléversement média';
$string['mediaupload:versioning'] = 'Versioning du média';
$string['mediaupload:versionnote'] = 'Note de version';
$string['mediaversions'] = 'Versions du média';
$string['metadatakeyvalues'] = 'Paires clé-valeur de métadonnées';
$string['mimetype'] = 'Type MIME';
$string['nocontentadvisories'] = 'Aucun avis de contenu';
$string['nofilteredrecords'] = 'Aucune trace ne correspond aux filtres.';
$string['nomediacollections'] = 'Aucune collection de médias.';
$string['nomediafound'] = 'Aucun média trouvé.';
$string['nomediarelations'] = 'Aucune relation de média.';
$string['nomediaversions'] = 'Aucune version de média.';
$string['nopermissiontoaddmedia'] = 'Vous n’avez pas la permission d’ajouter un média.';
$string['nopermissiontoeditmedia'] = 'Vous n’avez pas la permission de modifier ce média.';
$string['norelations'] = 'Aucune relation.';
$string['noversionfiles'] = 'Aucun fichier de version.';
$string['origin'] = 'Origine';
$string['passed'] = 'Réussi';
$string['primarysource'] = 'Source primaire';
$string['proofcontent'] = 'Contenu de preuve';
$string['proofgovernance'] = 'Gouvernance des preuves';
$string['provenance_ai_assisted'] = 'Assisté par IA';
$string['provenance_archive'] = 'Registre';
$string['provenance_assembly'] = 'Assemblée';
$string['provenance_challenge'] = 'Défi';
$string['provenance_human'] = 'Humain';
$string['provenance_imported'] = 'Importé';
$string['provenance_integrity'] = 'Intégrité';
$string['provenance_system'] = 'Système';
$string['provenancechain'] = 'Chaîne de provenance';
$string['provenancehashes'] = 'Empreintes de provenance';
$string['purgeexpiredexports'] = 'Purger les exports expirés';
$string['purpose'] = 'Finalité';
$string['rebuildcontentmarkerindex'] = 'Reconstruire l’index des marqueurs de contenu';
$string['recordsvisible'] = 'Traces visibles';
$string['redacted'] = 'Caviardé';
$string['refresharchive'] = 'Actualiser le registre';
$string['relatedrecords'] = 'Traces liées';
$string['relations'] = 'Relations';
$string['relationtype'] = 'Type de relation';
$string['remove'] = 'Retirer';
$string['requestmediareview'] = 'Demander une revue du média';
$string['requirescontextnotice'] = 'Ce contenu exige un contexte d’accompagnement.';
$string['restrictedcontent'] = 'Contenu restreint';
$string['restrictedcontentnotice'] = 'Ce contenu peut être sensible ou inapproprié pour certains publics.';
$string['restrictedculturalcontent'] = 'Contenu culturellement restreint';
$string['restricteddata'] = 'Données restreintes';
$string['restricteddatapresent'] = 'Données restreintes présentes';
$string['restrictedmedia'] = 'Média restreint';
$string['restrictednote'] = 'Note restreinte';
$string['restrictedproofnotice'] = 'Cette preuve contient des informations restreintes.';
$string['restrictedtarget'] = 'Cible restreinte';
$string['review'] = 'Revue';
$string['reviewedby'] = 'Revu par';
$string['rightsnote'] = 'Note sur les droits';
$string['rightsstatement'] = 'Déclaration de droits';
$string['rightsstatus'] = 'Statut des droits';
$string['rightsstatus:fair_use_reference'] = 'Référence d’usage équitable';
$string['rightsstatus:licensed_external'] = 'Licence externe';
$string['rightsstatus:open_license'] = 'Licence ouverte';
$string['rightsstatus:public_domain'] = 'Domaine public';
$string['rightsstatus:restricted_reference'] = 'Référence restreinte';
$string['rightsstatus:third_party_copyright'] = 'Droit d’auteur tiers';
$string['rightsstatus:unknown'] = 'Inconnu';
$string['saveexternalwork'] = 'Enregistrer l’œuvre externe';
$string['savemedia'] = 'Enregistrer le média';
$string['savemediarelation'] = 'Enregistrer la relation de média';
$string['searcharchive'] = 'Rechercher dans le registre';
$string['searcharchiveplaceholder'] = 'Rechercher dans le registre…';
$string['sortorder'] = 'Ordre de tri';
$string['sourcenote'] = 'Note de source';
$string['sourceownership:external_reference'] = 'Référence externe';
$string['sourceownership:member_submitted'] = 'Soumis par un membre';
$string['sourceownership:open_license'] = 'Licence ouverte';
$string['sourceownership:partner_submitted'] = 'Soumis par un partenaire';
$string['sourceownership:public_domain'] = 'Domaine public';
$string['sourceownership:third_party_copyright'] = 'Droit d’auteur tiers';
$string['sourceownership:uckk_commissioned'] = 'Commandé par UCKK';
$string['sourceownership:uckk_created'] = 'Créé par UCKK';
$string['sourceownership:unknown_source'] = 'Source inconnue';
$string['sources'] = 'Sources';
$string['status:deleted_soft'] = 'Supprimé logiquement';
$string['status:restricted'] = 'Restreint';
$string['status:submitted'] = 'Soumis';
$string['status:superseded'] = 'Remplacé';
$string['status_active'] = 'Actif';
$string['status_archived'] = 'Classé';
$string['status_contested'] = 'Contesté';
$string['status_deleted_soft'] = 'Supprimé logiquement';
$string['status_draft'] = 'Brouillon';
$string['status_invalidated'] = 'Invalidé';
$string['status_published'] = 'Publié';
$string['status_restricted'] = 'Restreint';
$string['status_submitted'] = 'Soumis';
$string['status_superseded'] = 'Remplacé';
$string['status_under_review'] = 'En revue';
$string['status_validated'] = 'Validé';
$string['targetid'] = 'ID de la cible';
$string['targettype'] = 'Type de cible';
$string['task:generatemediaderivatives'] = 'Générer les dérivés de médias';
$string['task:generatemediathumbnails'] = 'Générer les vignettes de médias';
$string['task:purgeexpiredexports'] = 'Purger les exports expirés';
$string['task:rebuildcontentmarkerindex'] = 'Reconstruire l’index des marqueurs de contenu';
$string['task_rebuild_media_search'] = 'Reconstruire la recherche média';
$string['taskgeneratemediathumbnails'] = 'Générer les vignettes de médias';
$string['teachingcontext'] = 'Contexte pédagogique';
$string['teachingnote'] = 'Note pédagogique';
$string['time'] = 'Temps';
$string['timemodified'] = 'Date de modification';
$string['toggledetails'] = 'Afficher ou masquer les détails';
$string['uckkarchive:addmedia'] = 'Ajouter des médias';
$string['uckkarchive:deletemedia'] = 'Supprimer les médias';
$string['uckkarchive:downloadmedia'] = 'Télécharger les médias';
$string['uckkarchive:editmedia'] = 'Modifier les médias';
$string['uckkarchive:exportmedia'] = 'Exporter les médias';
$string['uckkarchive:manageadvisories'] = 'Gérer les avis de contenu';
$string['uckkarchive:managecontentadvisories'] = 'Gérer les avis de contenu';
$string['uckkarchive:managemediacollections'] = 'Gérer les collections de médias';
$string['uckkarchive:reviewadvisories'] = 'Réviser les avis de contenu';
$string['uckkarchive:versionmedia'] = 'Versionner les médias';
$string['uckkarchive:viewadvisories'] = 'Voir les avis de contenu';
$string['uckkarchive:viewculturallyrestricted'] = 'Voir les contenus culturellement restreints';
$string['uckkarchive:viewmedia'] = 'Voir la Médiathèque';
$string['uckkarchive:viewrestrictedmedia'] = 'Voir les médias restreints';
$string['validationchecks'] = 'Vérifications de validation';
$string['validationevidence'] = 'Preuve de validation';
$string['validationreason'] = 'Raison de validation';
$string['validationstate_archived'] = 'Classé';
$string['validationstate_contested'] = 'Contesté';
$string['validationstate_human_reviewed'] = 'Revu humainement';
$string['validationstate_invalidated'] = 'Invalidé';
$string['validationstate_unverified'] = 'Non vérifié';
$string['validationstate_verified'] = 'Vérifié';
$string['versions'] = 'Versions';
$string['video'] = 'Vidéo';
$string['viewintegrityrecord'] = 'Voir la trace d’intégrité';
$string['viewsource'] = 'Voir la source';
$string['visibility:restricted_cultural'] = 'Restreinte culturelle';
$string['visibility_cohort'] = 'Cohorte';
$string['visibility_course'] = 'Cours';
$string['visibility_institution'] = 'Institution';
$string['visibility_private'] = 'Privée';
$string['visibility_program'] = 'Programme';
$string['visibility_public'] = 'Publique';
$string['visibility_restricted'] = 'Restreinte';
$string['visibility_restricted_cultural'] = 'Restreinte culturelle';
$string['visibility_restricted_integrity'] = 'Restreinte à l’intégrité';

// -----------------------------------------------------------------------------
// Chaînes requises par les modules AMD et les capacités d’œuvres externes.
// -----------------------------------------------------------------------------

$string['contentadvisory:loading'] = 'Chargement des avis de contenu…';
$string['contentadvisory:loaded'] = 'Avis de contenu chargés.';
$string['contentadvisory:loadfailed'] = 'Impossible de charger les avis de contenu.';
$string['contentmarker'] = 'Marqueur de contenu';
$string['deletemedia'] = 'Supprimer le média';
$string['deletemediaconfirm'] = 'Voulez-vous vraiment supprimer ce média ?';
$string['externalwork:loading'] = 'Chargement de l’œuvre externe…';
$string['externalwork:loaded'] = 'Œuvre externe chargée.';
$string['externalwork:loadfailed'] = 'Impossible de charger l’œuvre externe.';
$string['externalworks'] = 'Œuvres externes';
$string['externalworks:refreshing'] = 'Actualisation des œuvres externes…';
$string['externalworks:refreshed'] = 'Œuvres externes actualisées.';
$string['externalworks:refreshfailed'] = 'Impossible d’actualiser les œuvres externes.';
$string['media:loading'] = 'Chargement du média…';
$string['media:loaded'] = 'Média chargé.';
$string['media:loadfailed'] = 'Impossible de charger le média.';
$string['media:refreshing'] = 'Actualisation des médias…';
$string['media:refreshed'] = 'Médias actualisés.';
$string['media:refreshfailed'] = 'Impossible d’actualiser les médias.';
$string['mediacollection:loading'] = 'Chargement de la collection de médias…';
$string['mediacollection:loaded'] = 'Collection de médias chargée.';
$string['mediacollection:loadfailed'] = 'Impossible de charger la collection de médias.';
$string['mediacollections:refreshing'] = 'Actualisation des collections de médias…';
$string['mediacollections:refreshed'] = 'Collections de médias actualisées.';
$string['mediacollections:refreshfailed'] = 'Impossible d’actualiser les collections de médias.';
$string['mediaversions:loading'] = 'Chargement des versions du média…';
$string['mediaversions:loaded'] = 'Versions du média chargées.';
$string['mediaversions:loadfailed'] = 'Impossible de charger les versions du média.';
$string['medianotfound'] = 'Média introuvable.';
$string['noitemsselected'] = 'Aucun élément sélectionné.';
$string['uckkarchive:manageexternalworks'] = 'Gérer les œuvres externes';
$string['uckkarchive:viewexternalworks'] = 'Voir les œuvres externes';
$string['uckkarchive:addexternalworks'] = 'Ajouter des œuvres externes';
$string['uckkarchive:editexternalworks'] = 'Modifier les œuvres externes';
$string['uckkarchive:deleteexternalworks'] = 'Supprimer les œuvres externes';

// -----------------------------------------------------------------------------
// Éditeur de médiathèque.
// -----------------------------------------------------------------------------

$string['medialibraryeditor'] = 'Éditeur de médiathèque';
$string['medialibraryeditor_desc'] = 'Qualifier, contextualiser, relier, gouverner et valider les médias de la Médiathèque.';
$string['backtomedialibrary'] = 'Retour à la médiathèque';
$string['mediaeditorpreview'] = 'Aperçu du média';
$string['mediaeditorworkflow'] = 'Workflow';
$string['mediaeditorgovernance'] = 'Gouvernance';
$string['mediaeditoractions'] = 'Actions de l’éditeur';
$string['mediaeditorform'] = 'Formulaire de qualification média';
$string['mediaeditorform_desc'] = 'Modifier l’identité du média, sa source, ses droits, sa visibilité, son audience, ses indices d’avis de contenu et ses métadonnées.';
$string['mediaeditorstep_reception'] = 'Réception';
$string['mediaeditorstep_identification'] = 'Identification';
$string['mediaeditorstep_qualification'] = 'Qualification';
$string['mediaeditorstep_markers'] = 'Repères de passage';
$string['mediaeditorstep_advisories'] = 'Avis et protocoles';
$string['mediaeditorstep_relations'] = 'Relations';
$string['mediaeditorstep_validation'] = 'Validation';
$string['newmediarecord'] = 'Nouveau média';
$string['passagemarkers'] = 'Repères de passage';
$string['passagemarkers_desc'] = 'Pointer vers un passage précis d’une vidéo, d’un audio, d’un livre, d’un PDF, d’un site ou d’une œuvre externe.';
$string['managepassagemarkers'] = 'Gérer les repères de passage';
$string['mediaeditoradvisories_desc'] = 'Réviser les avertissements, avis culturels, protocoles culturels et conditions d’adéquation au public.';
$string['mediaeditorrelations_desc'] = 'Relier ce média à des collections, éléments de registre, versions, œuvres externes, preuves ou autres médias.';
$string['mediaeditorvalidation_desc'] = 'Suivre l’état de révision, la préparation à la publication, les restrictions et la contestabilité.';
$string['mediaeditorprovenance_desc'] = 'La provenance et l’audit restent gouvernés par les services serveur du Registraire.';
$string['mediacreated'] = 'Média créé.';
$string['mediaupdated'] = 'Média mis à jour.';

// -----------------------------------------------------------------------------
// Médiathèque publique.
// -----------------------------------------------------------------------------

$string['mediatheque'] = 'Médiathèque';
$string['mediatheque_title'] = 'Médiathèque UCKK';
$string['mediatheque_eyebrow'] = 'Médiathèque publique';
$string['mediatheque_summary'] = 'Explorer les médias publics, collections, œuvres externes et passages documentés de la Médiathèque UCKK.';

$string['mediatheque_explorer'] = 'Explorateur Médiathèque';
$string['mediatheque_explorer_title'] = 'Explorateur Médiathèque';
$string['mediatheque_explorer_desc'] = 'Rechercher et filtrer la Médiathèque publique. Les résultats sont filtrés selon la visibilité, les droits, les avis de contenu, les protocoles culturels et les politiques de publication et d’accès.';

$string['mediatheque_search'] = 'Rechercher dans la Médiathèque';
$string['mediatheque_search_placeholder'] = 'Rechercher par titre, description, source, mot-clé, collection ou passage';
$string['mediatheque_search_button'] = 'Rechercher';
$string['mediatheque_reset_filters'] = 'Réinitialiser les filtres';
$string['mediatheque_apply_filters'] = 'Appliquer les filtres';
$string['mediatheque_load_more'] = 'Charger plus de résultats';

$string['mediatheque_loading'] = 'Chargement des résultats de la Médiathèque…';
$string['mediatheque_loading_failed'] = 'Impossible de charger les résultats de la Médiathèque.';
$string['mediatheque_empty'] = 'Aucun média public ne correspond aux filtres.';
$string['mediatheque_empty_title'] = 'Aucun résultat';
$string['mediatheque_empty_desc'] = 'Essayez un autre terme de recherche ou retirez certains filtres.';

$string['mediatheque_results'] = 'Résultats de la Médiathèque';
$string['mediatheque_result_count'] = '{$a} résultat(s)';
$string['mediatheque_page'] = 'Page';
$string['mediatheque_perpage'] = 'Résultats par page';

$string['mediatheque_sort'] = 'Tri';
$string['mediatheque_sort_relevance'] = 'Pertinence';
$string['mediatheque_sort_newest'] = 'Plus récent';
$string['mediatheque_sort_title'] = 'Titre';
$string['mediatheque_sort_type'] = 'Type';

$string['mediatheque_filter_type'] = 'Type d’objet';
$string['mediatheque_filter_mediatype'] = 'Type de média';
$string['mediatheque_filter_collection'] = 'Collection';
$string['mediatheque_filter_tag'] = 'Mot-clé';
$string['mediatheque_filter_source'] = 'Source';
$string['mediatheque_filter_advisory'] = 'Avis de contenu';
$string['mediatheque_filter_cultural'] = 'Protocole culturel';
$string['mediatheque_filter_audience'] = 'Public';
$string['mediatheque_filter_language'] = 'Langue';
$string['mediatheque_filter_validation'] = 'Validation';

$string['mediatheque_filter_all'] = 'Tous';
$string['mediatheque_filter_none'] = 'Aucun';
$string['mediatheque_filter_has_advisory'] = 'Avec avis';
$string['mediatheque_filter_has_public_advisory'] = 'Avec avis public';
$string['mediatheque_filter_has_public_protocol'] = 'Avec protocole public';

$string['mediatheque_object_media'] = 'Média';
$string['mediatheque_object_collection'] = 'Collection';
$string['mediatheque_object_external_work'] = 'Œuvre externe';
$string['mediatheque_object_archive_item'] = 'Élément de registre lié';
$string['mediatheque_object_content_marker'] = 'Repère de passage';

$string['mediatheque_mediatype_video'] = 'Vidéo';
$string['mediatheque_mediatype_audio'] = 'Audio';
$string['mediatheque_mediatype_image'] = 'Image';
$string['mediatheque_mediatype_pdf'] = 'PDF';
$string['mediatheque_mediatype_document'] = 'Document';
$string['mediatheque_mediatype_book'] = 'Livre';
$string['mediatheque_mediatype_external_reference'] = 'Référence externe';
$string['mediatheque_mediatype_other'] = 'Autre';

$string['mediatheque_source_produced_by_uckk'] = 'Produit par UCKK';
$string['mediatheque_source_submitted_to_uckk'] = 'Soumis à UCKK';
$string['mediatheque_source_imported'] = 'Importé';
$string['mediatheque_source_external_reference_only'] = 'Référence externe seulement';
$string['mediatheque_source_unknown'] = 'Source inconnue';

$string['mediatheque_audience_general'] = 'Général';
$string['mediatheque_audience_guided'] = 'Guidé';
$string['mediatheque_audience_mature'] = 'Public averti';
$string['mediatheque_audience_restricted'] = 'Restreint';

$string['mediatheque_validation_unverified'] = 'Non vérifié';
$string['mediatheque_validation_human_reviewed'] = 'Révisé humainement';
$string['mediatheque_validation_verified'] = 'Vérifié';
$string['mediatheque_validation_archived'] = 'Classé';

$string['mediatheque_public_notice'] = 'La Médiathèque affiche seulement les notices publiques filtrées par les politiques d’accès.';
$string['mediatheque_restricted_notice'] = 'Certains contenus sont masqués ou résumés selon les droits, les avis de contenu, les protocoles culturels et les politiques de publication et d’accès.';
$string['mediatheque_policy_filtered_notice'] = 'Les résultats sont filtrés côté serveur par les politiques de publication et d’accès.';
$string['mediatheque_no_download_notice'] = 'Cette carte publique ne donne pas accès au fichier original.';
$string['mediatheque_external_reference_notice'] = 'Cette notice référence une œuvre externe. UCKK ne revendique pas la propriété du contenu externe.';

$string['mediatheque_action_view_detail'] = 'Voir les détails';
$string['mediatheque_action_view_file'] = 'Voir le fichier';
$string['mediatheque_action_download'] = 'Télécharger';
$string['mediatheque_action_open_external'] = 'Ouvrir la référence externe';

$string['mediatheque_badge_public'] = 'Public';
$string['mediatheque_badge_restricted'] = 'Restreint';
$string['mediatheque_badge_advisory'] = 'Avis';
$string['mediatheque_badge_cultural_protocol'] = 'Protocole culturel';
$string['mediatheque_badge_external_work'] = 'Œuvre externe';
$string['mediatheque_badge_passage_marker'] = 'Repère de passage';

$string['mediatheque_service_search'] = 'Rechercher dans la Médiathèque publique';
$string['mediatheque_service_error_invalidscope'] = 'Portée de recherche Médiathèque invalide.';
$string['mediatheque_service_error_invalidfilters'] = 'Filtres Médiathèque invalides.';
$string['mediatheque_service_error_unavailable'] = 'Le service de recherche de la Médiathèque est temporairement indisponible.';
$string['mediatheque_service_warning_policyfiltered'] = 'Certains résultats peuvent être masqués par les politiques de publication et d’accès.';
$string['mediatheque_service_warning_restrictedhidden'] = 'Le contenu restreint a été masqué de la réponse publique.';

$string['libraryadmin'] = 'Médiathèques et bridges';
$string['libraryadminintro'] = 'Chaque Univers-Cité utilise une médiathèque autonome par défaut. Une même médiathèque peut être rattachée à plusieurs sites, et des bridges directionnels peuvent exposer une médiathèque entière, une collection ou un média sans dupliquer le contenu.';
$string['libraryschemamissing'] = 'Le schéma des médiathèques autonomes n’est pas installé. Exécutez d’abord la mise à niveau Moodle.';
$string['libraries'] = 'Médiathèques';
$string['libraryslug'] = 'Identifiant de médiathèque';
$string['createlibrary'] = 'Créer une médiathèque';
$string['attachlibrarysite'] = 'Rattacher / partager une médiathèque avec une Univers-Cité';
$string['sitekey'] = 'Identifiant de l’Univers-Cité';
$string['primary'] = 'Principale';
$string['shared'] = 'Secondaire (non utilisé comme fonds primaire public)';
$string['assignmedialibrary'] = 'Déplacer un média vers son fonds d’origine';
$string['assigncollectionlibrary'] = 'Déplacer une collection vers son fonds d’origine';
$string['mediauuid'] = 'UUID du média';
$string['collectionuuid'] = 'UUID de la collection';
$string['librarybridges'] = 'Bridges entre médiathèques';
$string['createbridge'] = 'Créer un bridge';
$string['sourcelibrary'] = 'Médiathèque source';
$string['targetlibrary'] = 'Médiathèque cible';
$string['scopeuuid'] = 'UUID de la collection ou du média (vide pour une médiathèque entière)';
$string['wholelibrary'] = 'Médiathèque entière';
$string['libraryadminlink'] = 'Administrer les médiathèques et leurs bridges';
$string['privacy:metadata:uckkarchive_library'] = 'Registre des médiathèques publiques autonomes.';
$string['privacy:metadata:uckkarchive_library_site'] = 'Rattachements entre Univers-Cités et médiathèques.';
$string['privacy:metadata:uckkarchive_library_bridge'] = 'Bridges de partage explicite entre médiathèques.';
$string['libraryrole'] = 'Rôle de la médiathèque';
$string['bridgesource'] = 'Source';
$string['bridgetarget'] = 'Cible';
$string['bridgelabel'] = 'Libellé du bridge';
$string['librarysitemappings'] = 'Rattachements Univers-Cité ↔ médiathèque';
$string['uckkarchive:managelibraries'] = 'Gérer les médiathèques autonomes et leurs bridges';
