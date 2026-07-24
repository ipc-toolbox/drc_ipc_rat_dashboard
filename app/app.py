from shiny.express import input, render, ui
from shiny import reactive
#from shiny.ui import output_text  # <-- explicit import (not re-exported in shiny.express.ui)
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from shinywidgets import render_plotly
import urllib.request, urllib.parse, json, ssl
import numpy as np
#import shinyswatch

import sys
IS_WASM = sys.platform == "emscripten"

# ── Auto-synced encrypted partitions (GitHub Actions pipeline) ──# ⚠️ EDIT: point at your repo's data folder
SYNC_BASE_URL = "https://raw.githubusercontent.com/smanninformatics/ipc_rat_dash/main/data"


# Must match the "name" values in partitions.json
SYNC_PARTITIONS = {    
    "national":  "National (all provinces)",    
    "ituri":     "Ituri",    
    "nord-kivu": "Nord-Kivu",    
    "sud-kivu":  "Sud-Kivu",
    }

# Link to manifest for native cache deployment
ui.head_content(
    # Web App Manifest (Chrome, Edge, Android)
    ui.tags.link(rel="manifest", href="manifest.json"),
    ui.tags.meta(name="theme-color", content="#0d6efd"),

    # iOS Safari — uses its own proprietary tags (ignores manifest for install)
    ui.tags.meta(name="apple-mobile-web-app-capable", content="yes"),
    ui.tags.meta(name="apple-mobile-web-app-status-bar-style",
                 content="black-translucent"),
    ui.tags.meta(name="apple-mobile-web-app-title", content="IPC RAT"),
    ui.tags.link(rel="apple-touch-icon", href="icon-192.png"),

    # Prevents iOS from trying to phone-link numbers in scores
    ui.tags.meta(name="format-detection", content="telephone=no"),
)

# =============================================================
#                       GLOBAL THRESHOLDS
# =============================================================
CRITICAL_THRESHOLD = 50
READY_THRESHOLD    = 80

COLOR_CRITICAL = "#c0392b"
COLOR_AT_RISK  = "#f39c12"
COLOR_READY    = "#27ae60"


# =============================================================
#                       I18N / TRANSLATIONS
# =============================================================
LANG_CHOICES = {"en": "English", "fr": "Français", "es": "Español"}

TRANSLATIONS = {
    "en": {
        "language_label": "🌐 Language",
        "csv_standard": "📄 CSV Upload (Standard)",
        "csv_custom": "🔧 CSV Upload (Custom Mapping)",
        "kobo_api": "🌐 KoboToolbox API",
        "upload_csv": "Upload CSV File",
        "kobo_url": "Kobo Server URL",
        "asset_uid": "Asset UID",
        "api_token": "API Token",
        "fetch_data": "🚀 Fetch Data",
        "apply_mapping": "✅ Apply Mapping",
        "required_fields": "🏥 Required Fields",
        "total_score_section": "🎯 Total Score",
        "component_scores": "🧩 Component Scores",
        "upload_to_begin": "⬆️ Upload a CSV to begin mapping its columns.",
        "columns_detected": "✅ {n} columns detected. Review the auto-suggested matches.",
        "time_axis": "Time Axis",
        "reporting_date": "Reporting Date",
        "days_since_baseline": "Days Since Baseline",
        "assessment_num": "Assessment #",
        "facilities": "Facilities",
        "components": "Components",
        "critical_components": "Outbreak-Assessment Domains",
        "thresholds_info": "Unified thresholds: 🔴 ≤ 50, 🟡 51–79, 🟢 ≥ 80",
        "district": "🗺️ District",
        "subdistrict": "🗺️ Subdistrict",
        "all_option": "— All —",

        "network_title": "Summary View",
        "network_subtitle": "Multi-facility trajectories anchored to each facility's first assessment",
        "outbreak_title": "Outbreak Response",
        "outbreak_subtitle": "",
        "deep_dive_title": "Facility Deep Dive",
        "deep_dive_subtitle": "Detailed inspection of a single facility — change selection in the sidebar",

        "kpi_facilities_tracked": "Facilities Tracked",
        "kpi_avg_assessments": "Avg Assessments / Facility",
        "kpi_median_delta": "Median Δ Total Score",
        "kpi_median_followup": "Median Follow-up (days)",
        "kpi_ready": "Ready Facilities",
        "kpi_at_risk": "At Risk",
        "kpi_critical": "Critical",
        #"kpi_bundle": "Bundle Compliant",

        "card_total_traj": "📈 Total Score Trajectory — One Line per Facility",
        "card_delta_heatmap": "🟥🟩 Change from Baseline — Latest minus First Score",
        "card_summary": "📋 Facility Progress Summary (Baseline → Latest)",
        "card_readiness_index": "🚦 Outbreak Readiness Index — Latest Snapshot",
        "card_bundle_grid": "🟢🟡🔴 Assessment Domain Scores",
        "card_facility_map": "🗺️ Facility Map — Readiness by Location",
        "card_dispatch": "📋 Dispatch Decision Table",
        "card_snapshot": "📊 Single Assessment Snapshot",
        "card_diverging": "📊 Domain Change Since Baseline — Diverging View",

        "desc_total_traj": "Dashed lines mark the score thresholds: 🔴 ≤ 50  🟡 51–79  🟢 ≥ 80.",
        "desc_readiness_index": "Latest total score from each facility's most recent assessment.",
        "desc_bundle_grid": "One row per facility, one column per outbreak-assessment domain. Cells colored using score thresholds: 🔴 ≤ 50  🟡 51–79  🟢 ≥ 80.",
        "desc_facility_map": "Color = total score thresholds: 🔴 ≤ 50  🟡 51–79  🟢 ≥ 80.; size scales with score. Requires latitude/longitude columns.",
        "desc_dispatch": "Sortable facility list with facility status and specific gaps.",
        "desc_snapshot": "All domain scores for the selected assessment. Dashed lines mark score thresholds (🔴 ≤ 50, 🟢 ≥ 80).",
        "desc_diverging": "Red = regressions, green = improvements. Sorted biggest loss → biggest gain.",

        "facility_inspect": "🏥 Facility to Inspect",
        "specific_assessment": "📋 Specific Assessment (defaults to most recent)",

        "map_no_data": "No data loaded. Upload a CSV or fetch from Kobo to begin.",
        "map_no_coords": "🗺️ Map unavailable — facility coordinates not found.",
        "map_no_critical": "Select at least one outbreak-assessment domain.",
        "map_no_valid": "Coordinate columns are present but contain no valid points yet.",

        "status_critical_short": "🔴 Critical",
        "status_at_risk_short": "🟡 At Risk",
        "status_ready_short": "🟢 Ready",

        "col_facility": "Facility",
        "col_assessments": "Assessments",
        "col_baseline_date": "Baseline Date",
        "col_latest_date": "Latest Date",
        "col_followup_days": "Follow-up (days)",
        "col_baseline_total": "Baseline Total",
        "col_latest_total": "Latest Total",
        "col_delta_total": "Δ Total",
        "col_latest_status": "Latest Status",
        "col_readiness": "Readiness",
        "col_bundle_compliant": "Score Compliant",
        "col_critical_gaps": "Critical Gaps",
        "col_last_assessed": "Last Assessed",
        "col_status": "Status",
        "col_component": "Domain",
        "col_score": "Score",
        "col_delta_baseline": "Δ from Baseline",
        "label_total_score": "TOTAL SCORE",

        "regression": "◀ REGRESSION",
        "improvement": "IMPROVEMENT ▶",
        "need_2_assess": "Need at least 2 assessments for this facility.",
        "chart_baseline": "Baseline",
        "chart_critical_thresh": "Critical ≤ 50",
        "chart_ready_thresh": "Ready ≥ 80",
        "chart_score": "Score",
        "chart_total_score": "Total Score",
        "chart_readiness_axis": "Readiness (mean of critical components)",
        "chart_delta_score": "Δ Score (Latest − Baseline)",
        "assessment_n_date": "Assessment #{n} — {date}",
        "use_custom_baseline": "Use custom baseline anchor",
        "baseline_date_label": "Baseline Date",
        "buffer_weeks_label":  "Buffer (± weeks)",
        "kpi_since_baseline":  "Assessments Since Baseline",
        "kpi_30d":             "Assessments (Last 30 Days)",
        "kpi_7d":              "Assessments (Last 7 Days)",

        "kpi_total_assessments": "Total Assessments",
        "kpi_total_30d":         "Total — Last 30 Days",
        "kpi_total_7d":          "Total — Last 7 Days",
        "province": "🗺️ Province",
        "level": "🏷️ Facility Level",

        "trend_filter_label": "Filter by trend",
        "trend_all": "All",
        "trend_up": "📈 Increasing",
        "trend_down": "📉 Decreasing",
        "trend_flat": "➡️ Static",
        "start_date_label": "📅 Include data on/after",

        "kobo_sync": "🔄 Kobo (Auto-synced)",
        "sync_partition": "🗺️ Data Access Level",
        "sync_passphrase": "🔑 Access Passphrase",
        "sync_load": "📥 Load Data",
        "sync_note": "Data refreshes automatically via a secure pipeline. Enter the passphrase provided by your coordinator.",

        

    },

    "fr": {
        "language_label": "🌐 Langue",
        "csv_standard": "📄 Import CSV (Standard)",
        "csv_custom": "🔧 Import CSV (Mappage personnalisé)",
        "kobo_api": "🌐 API KoboToolbox",
        "upload_csv": "Téléverser un fichier CSV",
        "kobo_url": "URL du serveur Kobo",
        "asset_uid": "UID de l'actif",
        "api_token": "Jeton API",
        "fetch_data": "🚀 Récupérer les données",
        "apply_mapping": "✅ Appliquer le mappage",
        "required_fields": "🏥 Champs requis",
        "total_score_section": "🎯 Score total",
        "component_scores": "🧩 Scores des composants",
        "upload_to_begin": "⬆️ Téléversez un CSV pour commencer le mappage.",
        "columns_detected": "✅ {n} colonnes détectées. Vérifiez les correspondances suggérées.",
        "time_axis": "Axe temporel",
        "reporting_date": "Date du rapport",
        "days_since_baseline": "Jours depuis le départ",
        "assessment_num": "N° d'évaluation",
        "facilities": "Établissements",
        "components": "Composants",
        "critical_components": "Domaines d'évaluation de l'épidémie",
        "thresholds_info": "Seuils unifiés : 🔴 ≤ 50, 🟡 51–79, 🟢 ≥ 80",
        "district": "🗺️ District",
        "subdistrict": "🗺️ Sous-district",
        "all_option": "— Tous —",

        "network_title": "Vue réseau",
        "network_subtitle": "Trajectoires multi-établissements ancrées à la première évaluation",
        "outbreak_title": "Réponse aux épidémies",
        "outbreak_subtitle": "",
        "deep_dive_title": "Analyse détaillée d'un établissement",
        "deep_dive_subtitle": "Inspection détaillée d'un établissement — changer la sélection dans la barre latérale",

        "kpi_facilities_tracked": "Établissements suivis",
        "kpi_avg_assessments": "Moy. évaluations / établissement",
        "kpi_median_delta": "Médiane Δ Score total",
        "kpi_median_followup": "Suivi médian (jours)",
        "kpi_ready": "Établissements prêts",
        "kpi_at_risk": "À risque",
        "kpi_critical": "Critique",
        #"kpi_bundle": "Bundle conforme",

        "card_total_traj": "📈 Trajectoire du score total — Une ligne par établissement",
        "card_delta_heatmap": "🟥🟩 Évolution depuis le départ — Dernier moins premier score",
        "card_summary": "📋 Résumé des progrès par établissement (Initial → Dernier)",
        "card_readiness_index": "🚦 Indice de préparation aux épidémies — Dernier instantané",
        "card_bundle_grid": "🟢🟡🔴 Scores par domaine d'évaluation",
        "card_facility_map": "🗺️ Carte des établissements — Préparation par emplacement",
        "card_dispatch": "📋 Tableau de décision de déploiement",
        "card_snapshot": "📊 Instantané d'une évaluation",
        "card_diverging": "📊 Évolution des domaines depuis le départ — Vue divergente",

        "desc_total_traj": "Les lignes pointillées marquent les seuils de score : 🔴 ≤ 50  🟡 51–79  🟢 ≥ 80.",
        "desc_readiness_index": "Score total le plus récent de chaque établissement.",
        "desc_bundle_grid": "Une ligne par établissement, une colonne par composant critique. Cellules colorées selon les seuils de score : 🔴 ≤ 50  🟡 51–79  🟢 ≥ 80.",
        "desc_facility_map": "Couleur = seuils de score total : 🔴 ≤ 50  🟡 51–79  🟢 ≥ 80 ; la taille varie selon le score. Nécessite des colonnes latitude/longitude.",
        "desc_dispatch": "Liste triable des établissements avec le statut de l'établissement et les lacunes spécifiques.",
        "desc_snapshot": "Tous les scores par domaine pour l'évaluation sélectionnée. Les lignes pointillées marquent les seuils de score (🔴 ≤ 50, 🟢 ≥ 80).",
        "desc_diverging": "Rouge = régressions, vert = améliorations. Trié de la plus grande perte au plus grand gain.",

        "facility_inspect": "🏥 Établissement à inspecter",
        "specific_assessment": "📋 Évaluation spécifique (par défaut : la plus récente)",

        "map_no_data": "Aucune donnée chargée. Téléversez un CSV ou récupérez depuis Kobo.",
        "map_no_coords": "🗺️ Carte indisponible — coordonnées introuvables.",
        "map_no_critical": "Sélectionnez au moins un domaine d'évaluation de l'épidémie.",
        "map_no_valid": "Les colonnes de coordonnées existent mais ne contiennent pas de points valides.",

        "status_critical_short": "🔴 Critique",
        "status_at_risk_short": "🟡 À risque",
        "status_ready_short": "🟢 Prêt",

        "col_facility": "Établissement",
        "col_assessments": "Évaluations",
        "col_baseline_date": "Date initiale",
        "col_latest_date": "Dernière date",
        "col_followup_days": "Suivi (jours)",
        "col_baseline_total": "Total initial",
        "col_latest_total": "Dernier total",
        "col_delta_total": "Δ Total",
        "col_latest_status": "Statut actuel",
        "col_readiness": "Préparation",
        "col_bundle_compliant": "Score conforme",
        "col_critical_gaps": "Lacunes critiques",
        "col_last_assessed": "Dernière évaluation",
        "col_status": "Statut",
        "col_component": "Domaine",
        "col_score": "Score",
        "col_delta_baseline": "Δ depuis l'initial",
        "label_total_score": "SCORE TOTAL",

        "regression": "◀ RÉGRESSION",
        "improvement": "AMÉLIORATION ▶",
        "need_2_assess": "Au moins 2 évaluations sont nécessaires pour cet établissement.",
        "chart_baseline": "Initial",
        "chart_critical_thresh": "Critique ≤ 50",
        "chart_ready_thresh": "Prêt ≥ 80",
        "chart_score": "Score",
        "chart_total_score": "Score total",
        "chart_readiness_axis": "Préparation (moyenne des composants critiques)",
        "chart_delta_score": "Δ Score (Dernier − Initial)",
        "assessment_n_date": "Évaluation n°{n} — {date}",
        "use_custom_baseline": "Utiliser une date de référence personnalisée",
        "baseline_date_label": "Date de référence",
        "buffer_weeks_label":  "Tolérance (± semaines)",
        "kpi_since_baseline":  "Évaluations depuis le départ",
        "kpi_30d":             "Évaluations (30 derniers jours)",
        "kpi_7d":              "Évaluations (7 derniers jours)",
        "kpi_total_assessments": "Évaluations totales",
        "kpi_total_30d":         "Total — 30 derniers jours",
        "kpi_total_7d":          "Total — 7 derniers jours",
        "province": "🗺️ Province",
        "level": "🏷️ Niveau d'installation",

        "trend_filter_label": "Filtrer par tendance",
        "trend_all": "Tous",
        "trend_up": "📈 En hausse",
        "trend_down": "📉 En baisse",
        "trend_flat": "➡️ Stable",
        "start_date_label": "📅 Inclure les données à partir du",

        "kobo_sync": "🔄 Kobo (Synchronisation auto)",
        "sync_partition": "🗺️ Niveau d'accès aux données",
        "sync_passphrase": "🔑 Phrase d'accès",
        "sync_load": "📥 Charger les données",
        "sync_note": "Les données sont actualisées automatiquement via un pipeline sécurisé. Saisissez la phrase d'accès fournie par votre coordinateur.",

        

    },

    "es": {
        "language_label": "🌐 Idioma",
        "csv_standard": "📄 Carga CSV (Estándar)",
        "csv_custom": "🔧 Carga CSV (Mapeo personalizado)",
        "kobo_api": "🌐 API KoboToolbox",
        "upload_csv": "Subir archivo CSV",
        "kobo_url": "URL del servidor Kobo",
        "asset_uid": "UID del activo",
        "api_token": "Token API",
        "fetch_data": "🚀 Obtener datos",
        "apply_mapping": "✅ Aplicar mapeo",
        "required_fields": "🏥 Campos requeridos",
        "total_score_section": "🎯 Puntaje total",
        "component_scores": "🧩 Puntajes de componentes",
        "upload_to_begin": "⬆️ Suba un CSV para comenzar el mapeo.",
        "columns_detected": "✅ {n} columnas detectadas. Revise las coincidencias sugeridas.",
        "time_axis": "Eje temporal",
        "reporting_date": "Fecha del informe",
        "days_since_baseline": "Días desde el inicio",
        "assessment_num": "N° de evaluación",
        "facilities": "Instalaciones",
        "components": "Componentes",
        "critical_components": "Dominios de evaluación del brote",
        "thresholds_info": "Umbrales unificados: 🔴 ≤ 50, 🟡 51–79, 🟢 ≥ 80",
        "district": "🗺️ Distrito",
        "subdistrict": "🗺️ Subdistrito",
        "all_option": "— Todos —",

        "network_title": "Vista de red",
        "network_subtitle": "Trayectorias multi-instalación ancladas a la primera evaluación de cada una",
        "outbreak_title": "Respuesta al brote",
        "outbreak_subtitle": "",
        "deep_dive_title": "Análisis detallado de instalación",
        "deep_dive_subtitle": "Inspección detallada de una sola instalación — cambie la selección en la barra lateral",

        "kpi_facilities_tracked": "Instalaciones rastreadas",
        "kpi_avg_assessments": "Prom. evaluaciones / instalación",
        "kpi_median_delta": "Mediana Δ Puntaje total",
        "kpi_median_followup": "Seguimiento mediano (días)",
        "kpi_ready": "Instalaciones listas",
        "kpi_at_risk": "En riesgo",
        "kpi_critical": "Crítico",
        #"kpi_bundle": "Bundle conforme",

        "card_total_traj": "📈 Trayectoria del puntaje total — Una línea por instalación",
        "card_delta_heatmap": "🟥🟩 Cambio desde el inicio — Último menos primer puntaje",
        "card_summary": "📋 Resumen de progreso por instalación (Inicial → Último)",
        "card_readiness_index": "🚦 Índice de preparación ante brotes — Última instantánea",
        "card_bundle_grid": "🟢🟡🔴 Puntajes por dominio de evaluación",
        "card_facility_map": "🗺️ Mapa de instalaciones — Preparación por ubicación",
        "card_dispatch": "📋 Tabla de decisión de despliegue",
        "card_snapshot": "📊 Instantánea de una evaluación",
        "card_diverging": "📊 Cambio de dominios desde el inicio — Vista divergente",

        "desc_total_traj": "Las líneas discontinuas marcan los umbrales de puntaje: 🔴 ≤ 50  🟡 51–79  🟢 ≥ 80.",
        "desc_readiness_index": "Puntaje total más reciente de cada instalación.",
        "desc_bundle_grid": "Una fila por instalación, una columna por componente crítico. Celdas coloreadas según los umbrales de puntaje: 🔴 ≤ 50  🟡 51–79  🟢 ≥ 80.",
        "desc_facility_map": "Color = umbrales de puntaje total: 🔴 ≤ 50  🟡 51–79  🟢 ≥ 80; el tamaño varía según el puntaje. Requiere columnas de latitud/longitud.",
        "desc_dispatch": "Lista ordenable de instalaciones con el estado de la instalación y las brechas específicas.",
        "desc_snapshot": "Todos los puntajes por dominio de la evaluación seleccionada. Las líneas discontinuas marcan los umbrales de puntaje (🔴 ≤ 50, 🟢 ≥ 80).",
        "desc_diverging": "Rojo = regresiones, verde = mejoras. Ordenado de mayor pérdida a mayor ganancia.",

        "facility_inspect": "🏥 Instalación a inspeccionar",
        "specific_assessment": "📋 Evaluación específica (por defecto: la más reciente)",

        "map_no_data": "No hay datos cargados. Suba un CSV u obtenga datos de Kobo.",
        "map_no_coords": "🗺️ Mapa no disponible — coordenadas no encontradas.",
        "map_no_critical": "Seleccione al menos un dominio de evaluación del brote.",
        "map_no_valid": "Las columnas de coordenadas existen pero no contienen puntos válidos.",

        "status_critical_short": "🔴 Crítico",
        "status_at_risk_short": "🟡 En riesgo",
        "status_ready_short": "🟢 Listo",

        "col_facility": "Instalación",
        "col_assessments": "Evaluaciones",
        "col_baseline_date": "Fecha inicial",
        "col_latest_date": "Última fecha",
        "col_followup_days": "Seguimiento (días)",
        "col_baseline_total": "Total inicial",
        "col_latest_total": "Último total",
        "col_delta_total": "Δ Total",
        "col_latest_status": "Estado actual",
        "col_readiness": "Preparación",
        "col_bundle_compliant": "Puntaje conforme",
        "col_critical_gaps": "Brechas críticas",
        "col_last_assessed": "Última evaluación",
        "col_status": "Estado",
        "col_component": "Dominio",
        "col_score": "Puntaje",
        "col_delta_baseline": "Δ desde el inicio",
        "label_total_score": "PUNTAJE TOTAL",

        "regression": "◀ REGRESIÓN",
        "improvement": "MEJORA ▶",
        "need_2_assess": "Se necesitan al menos 2 evaluaciones para esta instalación.",
        "chart_baseline": "Inicial",
        "chart_critical_thresh": "Crítico ≤ 50",
        "chart_ready_thresh": "Listo ≥ 80",
        "chart_score": "Puntaje",
        "chart_total_score": "Puntaje total",
        "chart_readiness_axis": "Preparación (promedio de componentes críticos)",
        "chart_delta_score": "Δ Puntaje (Último − Inicial)",
        "assessment_n_date": "Evaluación N° {n} — {date}",
        "use_custom_baseline": "Usar fecha de referencia personalizada",
        "baseline_date_label": "Fecha de referencia",
        "buffer_weeks_label":  "Tolerancia (± semanas)",
        "kpi_since_baseline":  "Evaluaciones desde el inicio",
        "kpi_30d":             "Evaluaciones (últimos 30 días)",
        "kpi_7d":              "Evaluaciones (últimos 7 días)",
        "kpi_total_assessments": "Evaluaciones totales",
        "kpi_total_30d":         "Total — Últimos 30 días",
        "kpi_total_7d":          "Total — Últimos 7 días",
        "province": "🗺️ Provincia",
        "level": "🏷️ Nivel del establecimiento",

        "trend_filter_label": "Filtrar por tendencia",
        "trend_all": "Todos",
        "trend_up": "📈 En aumento",
        "trend_down": "📉 En descenso",
        "trend_flat": "➡️ Estable",
        "start_date_label": "📅 Incluir datos desde",

        "kobo_sync": "🔄 Kobo (Sincronización automática)",
        "sync_partition": "🗺️ Nivel de acceso a datos",
        "sync_passphrase": "🔑 Frase de acceso",
        "sync_load": "📥 Cargar datos",
        "sync_note": "Los datos se actualizan automáticamente mediante un canal seguro. Ingrese la frase de acceso proporcionada por su coordinador.",

    },
}


def t(key: str, **kwargs) -> str:
    """Translate `key` using current input.language(). Falls back to English."""
    try:
        lang = input.language()
    except Exception:
        lang = "en"
    table = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = table.get(key) or TRANSLATIONS["en"].get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


# ----- Column definitions -----
# Maximum raw score per section — derived from the form's yes/no item count.
# These sum to 62, which matches the form's score_total_brut denominator.
SECTION_MAX = {
    "score_s1":  3,   "score_s2":  2,   "score_s3":  4,   "score_s4":  6,
    "score_s5":  9,   "score_s6":  1,   "score_s7":  4,   "score_s8":  8,
    "score_s9":  4,   "score_s10": 2,   "score_s11": 2,   "score_s12": 2,
    "score_s13": 4,   "score_s14": 3,   "score_s15": 3,   "score_s16": 3,
    "score_s17": 2,
}

COMPONENT_COLS = list(SECTION_MAX.keys())

COMPONENT_LABELS_I18N = {
    "en": {
        "score_s1":  "1. IPC Committee",
        "score_s2":  "2. Staff Training",
        "score_s3":  "3. Hand Hygiene",
        "score_s4":  "4. Screening / Triage",
        "score_s5":  "5. Isolation",
        "score_s6":  "6. PPE",
        "score_s7":  "7. Injection Safety",
        "score_s8":  "8. Env. Cleaning",
        "score_s9":  "9. Decontamination",
        "score_s10": "10. Post-exposure",
        "score_s11": "11. Patient Mgmt",
        "score_s12": "12. Patient Placement",
        "score_s13": "13. Sanitation",
        "score_s14": "14. Water Supply",
        "score_s15": "15. Waste Mgmt (Solid)",
        "score_s16": "16. Waste Mgmt (Liquid)",
        "score_s17": "17. Dead Body Mgmt",
    },
    "fr": {
        "score_s1":  "1. Comité PCI",
        "score_s2":  "2. Formation",
        "score_s3":  "3. Hygiène des mains",
        "score_s4":  "4. Dépistage",
        "score_s5":  "5. Isolement",
        "score_s6":  "6. EPI",
        "score_s7":  "7. Sécurité injections",
        "score_s8":  "8. Nettoyage env.",
        "score_s9":  "9. Décontamination",
        "score_s10": "10. Post-exposition",
        "score_s11": "11. Gestion patients",
        "score_s12": "12. Placement patients",
        "score_s13": "13. Assainissement",
        "score_s14": "14. Eau",
        "score_s15": "15. Déchets solides",
        "score_s16": "16. Déchets liquides",
        "score_s17": "17. Gestion des corps",
    },
    "es": {
        "score_s1":  "1. Comité IPC",
        "score_s2":  "2. Capacitación",
        "score_s3":  "3. Higiene de manos",
        "score_s4":  "4. Detección",
        "score_s5":  "5. Aislamiento",
        "score_s6":  "6. EPP",
        "score_s7":  "7. Seguridad inyecciones",
        "score_s8":  "8. Limpieza ambiental",
        "score_s9":  "9. Descontaminación",
        "score_s10": "10. Post-exposición",
        "score_s11": "11. Gestión pacientes",
        "score_s12": "12. Ubicación pacientes",
        "score_s13": "13. Saneamiento",
        "score_s14": "14. Suministro de agua",
        "score_s15": "15. Residuos sólidos",
        "score_s16": "16. Residuos líquidos",
        "score_s17": "17. Gestión de cuerpos",
    },
}
COMPONENT_LABELS = COMPONENT_LABELS_I18N["en"]   # back-compat

SCORE_TOTAL   = "score_pct"                       # already a percentage in new CSV
FACILITY_COL  = "nom_etablissement"
DATE_COL      = "date_evaluation"
LATITUDE_COL  = "_coordonnees_gps_latitude"
LONGITUDE_COL = "_coordonnees_gps_longitude"
FACILITY_OTHER_COL = "nom_etablissement_autre"
OTHER_VALUES = {"autre", "other", "autres", "others"}   # matched case-insensitively

# NEW: geographic grouping columns
DISTRICT_COL    = "district"
SUBDISTRICT_COL = "sous_district"
PROVINCE_COL = "province"
LEVEL_COL    = "niveau_installation"

# NEW: header renames applied to *every* dataset (standard CSV + Kobo)
#STANDARD_RENAME = {
#    "district":      DISTRICT_COL,      # passthrough (kept for clarity)
#    "sous_district": SUBDISTRICT_COL,   # the actual remap you asked for
#}


# =============================================================
#                     HELPERS
# =============================================================
def _coerce(df):
    df = _resolve_other_facilities(df)

    if DATE_COL in df.columns:
        df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")

    # Coerce everything numeric we care about
    numeric_targets = COMPONENT_COLS + [SCORE_TOTAL, "score_total_brut",
                                        LATITUDE_COL, LONGITUDE_COL]
    for c in [c for c in numeric_targets if c in df.columns]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Convert each component's raw score → percentage (0–100), in place.
    # If a column is already > 100 we assume it was percentage-scaled by an
    # earlier load and skip (idempotent / safe for re-coerce).
    for col, max_score in SECTION_MAX.items():
        if col in df.columns and max_score > 0:
            raw_max = df[col].max(skipna=True)
            if pd.notna(raw_max) and raw_max <= max_score + 0.5:
                df[col] = (df[col] / max_score * 100).round(1)

    return df

def _resolve_other_facilities(df):
    """Where facility name is 'autre'/'other' and a free-text name exists,
    replace it with 'Autre - <free text>' so each unlisted facility is unique
    (and visibly flagged for follow-up). Idempotent: already-resolved names
    no longer match OTHER_VALUES, so re-coercing is safe."""
    if FACILITY_COL not in df.columns or FACILITY_OTHER_COL not in df.columns:
        return df

    fac      = df[FACILITY_COL].astype(str).str.strip()
    is_other = fac.str.lower().isin(OTHER_VALUES)
    if not is_other.any():
        return df

    # Light normalization of the free text so trivial variants don't split
    names = (df[FACILITY_OTHER_COL].astype(str)
               .str.strip()
               .str.replace(r"\s+", " ", regex=True))
    has_name = is_other & names.notna() & (names != "") & (names.str.lower() != "nan")

    # Standardized prefix — NOT the original token, so 'Autre'/'other'/'AUTRE'
    # rows for the same facility all produce the identical resolved name
    df.loc[has_name, FACILITY_COL] = "Autre - " + names[has_name]
    return df

def _read_csv_robust(path):
    for sep in [",", ";", "\t"]:
        for enc in ["utf-8-sig", "utf-8", "latin-1"]:
            try:
                tmp = pd.read_csv(path, sep=sep, encoding=enc)
                if tmp.shape[1] > 1:
                    return tmp
            except Exception:
                continue
    return None


def fetch_kobo_data(server_url, asset_uid, token, page_size=30000):
    server_url = server_url.rstrip("/")
    url = f"{server_url}/api/v2/assets/{asset_uid}/data.json?format=json&limit={page_size}"
    headers = {"Authorization": f"Token {token}"}
    out = []
    while url:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=90, context=ssl.create_default_context()) as r:
            payload = json.loads(r.read().decode("utf-8"))
        out.extend(payload.get("results", []))
        url = payload.get("next")
    return pd.json_normalize(out) if out else pd.DataFrame()


SUGGEST_KEYWORDS = {
    FACILITY_COL:  ["nom_etablissement", "etablissement", "facility_name",
                    "facility", "hospital", "structure", "site", "nom"],
    FACILITY_OTHER_COL: ["nom_etablissement_autre", "etablissement_autre",
                     "facility_other", "facility_name_other", "autre"],
    DATE_COL:      ["date_evaluation", "date_evaluation", "reporting_date",
                    "date"],
    SCORE_TOTAL:   ["score_pct", "score_pourcentage", "score_percent",
                    "pct", "score_total"],
    LATITUDE_COL:  ["coordonnees_gps_latitude", "latitude", "_lat",
                    "lat_dd", "gps_latitude"],
    LONGITUDE_COL: ["coordonnees_gps_longitude", "longitude", "_lon",
                    "_lng", "gps_longitude"],
    DISTRICT_COL:    ["district"],
    SUBDISTRICT_COL: ["sous_district", "subdistrict", "sub_district"],
    PROVINCE_COL: ["province"],
    LEVEL_COL:    ["niveau_installation", "niveau", "level",
               "facility_level", "type_installation"],
    
    # Component score columns map by their exact names; the keyword matcher
    # gives them a perfect score when the column name equals score_sN.
    **{f"score_s{i}": [f"score_s{i}", f"s{i}_score"] for i in range(1, 18)},
}

NONE_OPTION = "— None —"
ALL_OPTION  = "__ALL__"   # NEW: stable value; label is translated



def best_match(target_key: str, columns: list[str]) -> str:
    keywords = SUGGEST_KEYWORDS.get(target_key, [])
    if not keywords or not columns:
        return NONE_OPTION
    norm = {c: c.lower().replace(" ", "_").replace("-", "_") for c in columns}
    best, best_score = NONE_OPTION, 0
    for col, n in norm.items():
        score = sum(len(kw) for kw in keywords if kw.lower() in n)
        if n == target_key.lower():
            score += 100
        if score > best_score:
            best, best_score = col, score
    return best


MAP_TARGETS = [
    (FACILITY_COL,  "🏥 Facility Name (required)"),
    (FACILITY_OTHER_COL, "🏥 Facility Name — Other (free text, optional)"),
    (DATE_COL,      "📅 Reporting Date (required)"),
    (PROVINCE_COL,    "🗺️ Province (optional)"),
    (DISTRICT_COL,    "🗺️ District (optional)"),      
    (SUBDISTRICT_COL, "🗺️ Subdistrict (optional)"),
    (LEVEL_COL,       "🏷️ Facility Level (optional)"),
    (LATITUDE_COL,  "📍 Latitude (optional, for map)"),
    (LONGITUDE_COL, "📍 Longitude (optional, for map)"),
    (SCORE_TOTAL,   "🎯 Total Score"),
] + [(c, COMPONENT_LABELS[c]) for c in COMPONENT_COLS]

#Cascading filter helper
# Cascade order: each filter is constrained by all the ones before it
CASCADE_LEVELS = [
    (PROVINCE_COL,    "province"),
    (DISTRICT_COL,    "district"),
    (SUBDISTRICT_COL, "subdistrict"),
    (LEVEL_COL,       "level"),
]

def _apply_cascade(df, levels):
    """Filter df by the current value of each (column, input_id) in `levels`."""
    for col, input_id in levels:
        if col not in df.columns:
            continue
        try:
            val = input[input_id]()
        except Exception:
            val = None
        if val and val != ALL_OPTION:
            df = df[df[col].astype(str) == val]
    return df

def details_panel(title: str, *children, open: bool = False):
    return ui.tags.details(
        ui.tags.summary(
            title,
            style=(
                "cursor:pointer; font-weight:600; padding:8px 4px; "
                "border-bottom:1px solid #e0e0e0; margin-top:6px;"
            ),
        ),
        ui.div(*children, style="padding: 8px 4px 12px 4px;"),
        open=open,
    )


def add_time_anchors(df: pd.DataFrame,
                    baseline_date=None,
                    buffer_weeks: int = 4) -> pd.DataFrame:
    """
    Add 'Days Since Baseline' and 'Assessment #' columns.

    - If baseline_date is None: each facility's baseline = its own earliest assessment.
    - If baseline_date is provided: for each facility, find the EARLIEST assessment
      within [baseline_date - buffer_weeks, baseline_date + buffer_weeks].
      Facilities with no assessment in that window fall back to their own earliest.
      Pre-baseline assessments are dropped.
    """
    if df is None or df.empty or FACILITY_COL not in df.columns or DATE_COL not in df.columns:
        return df
    df = df.dropna(subset=[DATE_COL]).copy()
    df = df.sort_values([FACILITY_COL, DATE_COL])

    if baseline_date is None:
        baselines = df.groupby(FACILITY_COL)[DATE_COL].min()
    else:
        target = pd.Timestamp(baseline_date)
        buf = pd.Timedelta(weeks=int(buffer_weeks))
        win_start, win_end = target - buf, target + buf

        def _baseline_for(group):
            in_win = group[(group[DATE_COL] >= win_start) &
                           (group[DATE_COL] <= win_end)]
            return in_win[DATE_COL].min() if not in_win.empty else group[DATE_COL].min()

        baselines = df.groupby(FACILITY_COL).apply(_baseline_for)

    df["_baseline_date"] = df[FACILITY_COL].map(baselines)

    # When a custom baseline is in effect, drop pre-baseline rows
    if baseline_date is not None:
        df = df[df[DATE_COL] >= df["_baseline_date"]].copy()

    df["Days Since Baseline"] = (df[DATE_COL] - df["_baseline_date"]).dt.days
    df["Assessment #"]        = df.groupby(FACILITY_COL).cumcount() + 1
    df = df.drop(columns=["_baseline_date"])
    return df


def x_axis_map():
    return {
        "date": (DATE_COL,              t("reporting_date")),
        "days": ("Days Since Baseline", t("days_since_baseline")),
        "num":  ("Assessment #",        t("assessment_num")),
    }


def first_last_per_facility(df, cols):
    df = df.sort_values(DATE_COL)
    g = df.groupby(FACILITY_COL)
    first = g[cols].first()
    last  = g[cols].last()
    return first, last, (last - first)


def section_banner(emoji: str, title: str, subtitle: str, color: str = "#0d6efd"):
    return ui.div(
        ui.div(
            ui.span(emoji, style="font-size:2.2rem; margin-right:14px;"),
            ui.div(
                ui.h3(
                    title, class_="mb-0",
                    style=f"color:{color}; font-weight:700; letter-spacing:.3px;",
                ),
                ui.tags.small(subtitle, class_="text-muted"),
            ),
            style="display:flex; align-items:center;",
        ),
        ui.tags.hr(
            style=f"border:0; border-top:3px solid {color}; opacity:1; margin:8px 0 0 0;",
        ),
        class_="mt-3 mb-3",
    )

def _ordered_critical(df=None):
    """Selected critical components in canonical COMPONENT_COLS order.
    Optionally filters to columns present in df."""
    sel = set(input.critical_components() or [])
    ordered = [c for c in COMPONENT_COLS if c in sel]
    if df is not None:
        ordered = [c for c in ordered if c in df.columns]
    return ordered

def outbreak_readiness(df, critical_cols):
    if df is None or df.empty or not critical_cols:
        return pd.DataFrame()
    cols = [c for c in critical_cols if c in df.columns]
    if not cols:
        return pd.DataFrame()

    # If every known component is selected AND the source Total Score column exists,
    # use the authoritative Total Score as the Readiness value instead of recomputing
    # an unweighted mean. This keeps Readiness consistent with how the underlying
    # instrument aggregates scores (which may be weighted differently than a mean).
    use_total_score = (
        set(COMPONENT_COLS).issubset(set(critical_cols))
        and SCORE_TOTAL in df.columns
    )

    latest = df.sort_values(DATE_COL).groupby(FACILITY_COL).tail(1)
    latest = latest.set_index(FACILITY_COL)

    rows = []
    for fac, row in latest.iterrows():
        scores = row[cols].astype(float)
        valid = scores.dropna()
        if valid.empty:
            continue

        # ---- Readiness ----
        if use_total_score and pd.notna(row.get(SCORE_TOTAL)):
            readiness = float(row[SCORE_TOTAL])
        else:
            readiness = float(valid.mean())

        below_ready = scores[scores < READY_THRESHOLD].dropna().index.tolist()

        # ---- Status driven by Total Score (unchanged) ----
        total_score = row.get(SCORE_TOTAL) if SCORE_TOTAL in row.index else None
        if pd.isna(total_score) or total_score is None:
            status, total_val = "—", None
        else:
            total_val = float(total_score)
            if total_val <= CRITICAL_THRESHOLD:
                status = "🔴 CRITICAL"
            elif total_val < READY_THRESHOLD:
                status = "🟡 AT RISK"
            else:
                status = "🟢 READY"

        rows.append({
            "Facility":      fac,
            "Readiness":     round(readiness, 1),
            "Critical Gaps": ", ".join(COMPONENT_LABELS.get(c, c) for c in below_ready) or "—",
            "Last Assessed": row[DATE_COL].date(),
            "Status":        status,
        })
    return pd.DataFrame(rows).sort_values("Readiness", na_position="last")


def _translate_status(s: str) -> str:
    return {
        "🔴 CRITICAL": t("status_critical_short"),
        "🟡 AT RISK":  t("status_at_risk_short"),
        "🟢 READY":    t("status_ready_short"),
    }.get(s, s)


def _map_placeholder(message_html: str):
    return go.Figure().update_layout(
        annotations=[dict(
            text=message_html, showarrow=False,
            x=0.5, y=0.5, xref="paper", yref="paper",
            font=dict(size=13, color="#666"),
            align="center",
        )],
        height=500,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="#f8f9fa",
        margin=dict(l=10, r=10, t=10, b=10),
    )

def component_labels() -> dict:
    """Component labels for the current language (falls back to English).
    Must be called inside a reactive/render context to track language changes."""
    try:
        lang = input.language()
    except Exception:
        lang = "en"
    return COMPONENT_LABELS_I18N.get(lang, COMPONENT_LABELS_I18N["en"])

async def fetch_kobo_data_wasm(server_url, asset_uid, token, page_size=30000):
    """Fetch KoboToolbox data using the browser's native fetch API (Pyodide only)."""
    import js
    from pyodide.ffi import to_js

    server_url = server_url.rstrip("/")
    url = (f"{server_url}/api/v2/assets/{asset_uid}"
           f"/data.json?format=json&limit={page_size}")
    out = []
    page = 0

    while url:
        page += 1
        options = to_js(
            {
                "method": "GET",
                "headers": {
                    "Authorization": f"Token {token}",
                    "Accept": "application/json",
                },
            },
            dict_converter=js.Object.fromEntries,
        )

        try:
            response = await js.fetch(url, options)
        except Exception as e:
            msg = str(e).lower()
            if any(w in msg for w in ("cors", "fetch", "network", "failed")):
                raise Exception(
                    "CORS blocked — the KoboToolbox server must allow browser requests. "
                    "Public instances (kf.kobotoolbox.org, kobo.humanitarianresponse.info) "
                    "support this. For private instances, ask your admin to enable CORS."
                )
            raise Exception(f"Network error: {e}")

        status = int(response.status)
        if not response.ok:
            raise Exception({
                401: "Authentication failed — check your API token.",
                403: "Permission denied — verify your token and asset UID.",
                404: "Asset not found — check your asset UID.",
            }.get(status, f"Server error: HTTP {status}"))

        text = await response.text()
        payload = json.loads(text)
        out.extend(payload.get("results", []))
        url = payload.get("next")  # KoboToolbox paginates via 'next'

    return pd.json_normalize(out) if out else pd.DataFrame()

# ── Encrypted partition loading (runs inside the Pyodide worker) ─────────
async def _fetch_partition_bytes(url: str):
    """Fetch the .enc blob. Saves a copy in the Cache API for offline use;
    falls back to that copy when the network is unavailable.
    Returns (blob_bytes, from_cache)."""
    import js
    cache = await js.caches.open("ipc-rat-partitions")
    try:
        resp = await js.fetch(url)
    except Exception:
        # Network failure → try the offline cache
        cached = await cache.match(url)
        if not cached:
            raise Exception("OFFLINE_NO_CACHE")
        buf = await cached.arrayBuffer()
        return bytes(js.Uint8Array.new(buf).to_py()), True

    if not resp.ok:
        raise Exception(
            f"HTTP {int(resp.status)} — partition file not found. "
            "Has the GitHub Action run successfully?"
        )
    await cache.put(url, resp.clone())        # store for offline use
    buf = await resp.arrayBuffer()
    return bytes(js.Uint8Array.new(buf).to_py()), False


def _decrypt_partition(blob: bytes, passphrase: str) -> str:
    """PBKDF2 → AES-256-GCM decrypt → gunzip.
    Exact mirror of encrypt() in scripts/fetch_kobo.py:
    16B salt | 12B nonce | ciphertext(+tag), PBKDF2-SHA256 @ 200k iterations."""
    import gzip as _gz
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.exceptions import InvalidTag

    salt, nonce, ct = blob[:16], blob[16:28], blob[28:]
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                     salt=salt, iterations=200_000)
    key = kdf.derive(passphrase.encode("utf-8"))
    try:
        plaintext = AESGCM(key).decrypt(nonce, ct, None)
    except InvalidTag:
        raise Exception("WRONG_PASSPHRASE")
    return _gz.decompress(plaintext).decode("utf-8")

# =============================================================
#                           REACTIVES
# =============================================================
kobo_data           = reactive.value(None)
kobo_status_msg     = reactive.value(None)
kobo_sync_msg = reactive.value(None)
kobo_cors_msg = reactive.value(None)
custom_csv_raw      = reactive.value(None)
custom_csv_mapped   = reactive.value(None)
mapping_status_msg  = reactive.value(None)


@reactive.effect
def _read_custom_csv():
    f = input.file_custom()
    if not f:
        return
    df = _read_csv_robust(f[0]["datapath"])
    if df is None:
        mapping_status_msg.set(("err", "Could not read the CSV (encoding/delimiter)."))
        custom_csv_raw.set(None)
        return
    custom_csv_raw.set(df)
    custom_csv_mapped.set(None)
    mapping_status_msg.set(("info", f"📄 Loaded {len(df):,} rows, {df.shape[1]} columns."))


@reactive.effect
@reactive.event(input.apply_mapping)
def _apply_mapping():
    df = custom_csv_raw.get()
    if df is None:
        mapping_status_msg.set(("err", "No file uploaded yet."))
        return

    rename: dict[str, str] = {}
    unmapped_targets: list[str] = []

    for target_key, label in MAP_TARGETS:
        try:
            source_col = input[f"map__{target_key}"]()
        except Exception:
            source_col = None

        if source_col and source_col != NONE_OPTION and source_col in df.columns:
            if source_col in rename:
                new_col = f"__copy__{target_key}"
                df[new_col] = df[source_col]
                rename[new_col] = target_key
            else:
                rename[source_col] = target_key
        else:
            unmapped_targets.append(label)

    if FACILITY_COL not in rename.values() or DATE_COL not in rename.values():
        mapping_status_msg.set((
            "err",
            "❌ Facility Name and Reporting Date are required. Please map them.",
        ))
        return

    mapped = df.rename(columns=rename)
    mapped = _coerce(mapped)
    custom_csv_mapped.set(mapped)
    mapping_status_msg.set(("ok", f"✅ Mapping applied — {len(rename)} columns mapped"))


@reactive.effect
@reactive.event(input.kobo_fetch)
async def _fetch_kobo():
    if IS_WASM:
        kobo_status_msg.set(("err",
            "Live API fetch isn't available in the browser version "
            "(the Kobo server blocks cross-origin requests). "
            "Use '🔄 Kobo (Auto-synced)' instead."))
        return
    url   = (input.kobo_url()   or "").strip()
    asset = (input.kobo_asset() or "").strip()
    token = (input.kobo_token() or "").strip()
    if not (url and asset and token):
        kobo_status_msg.set(("err", "Fill in all Kobo fields."))
        return
    kobo_status_msg.set(("info", "⏳ Fetching…"))
    try:
        if IS_WASM:
            df = await fetch_kobo_data_wasm(url, asset, token)
        else:
            df = fetch_kobo_data(url, asset, token)   # existing synchronous path
        if df.empty:
            kobo_status_msg.set(("err", "No records returned."))
            kobo_data.set(None)
            return
        kobo_data.set(df)
        kobo_status_msg.set(("ok", f"✅ Loaded {len(df):,} records."))
    except Exception as e:
        kobo_status_msg.set(("err", str(e)))
        kobo_data.set(None)


@reactive.effect
@reactive.event(input.kobo_cors_check)
async def _kobo_cors_check():
    """Quick preflight to test if the Kobo server allows browser requests."""
    url   = (input.kobo_url()   or "").strip()
    asset = (input.kobo_asset() or "").strip()
    token = (input.kobo_token() or "").strip()
    if not (url and asset and token):
        kobo_cors_msg.set(("err", "Fill in all fields before testing."))
        return
    if not IS_WASM:
        kobo_cors_msg.set(("info", "CORS test only applies to the browser-hosted version."))
        return

    kobo_cors_msg.set(("info", "⏳ Testing connection…"))
    import js
    from pyodide.ffi import to_js
    test_url = (f"{url.rstrip('/')}/api/v2/assets/{asset}"
                f"/data.json?format=json&limit=1")
    try:
        options = to_js(
            {"method": "GET",
             "headers": {"Authorization": f"Token {token}", "Accept": "application/json"}},
            dict_converter=js.Object.fromEntries,
        )
        response = await js.fetch(test_url, options)
        status = int(response.status)
        if response.ok:
            kobo_cors_msg.set(("ok",
                f"✅ Connection successful (HTTP {status}) — "
                "this server supports browser requests."))
        elif status == 401:
            kobo_cors_msg.set(("err", "⚠️ Reachable but token rejected (HTTP 401). "
                                      "CORS is working — check your API token."))
        elif status == 404:
            kobo_cors_msg.set(("err", "⚠️ Reachable but asset not found (HTTP 404). "
                                      "CORS is working — check your asset UID."))
        else:
            kobo_cors_msg.set(("err", f"⚠️ Reachable — HTTP {status}."))
    except Exception as e:
        msg = str(e).lower()
        if any(w in msg for w in ("cors", "network", "failed", "fetch")):
            kobo_cors_msg.set(("err",
                "❌ CORS blocked — this server does not allow browser requests. "
                "Contact your KoboToolbox admin to enable CORS, or download "
                "data manually and use CSV upload."))
        else:
            kobo_cors_msg.set(("err", f"Connection error: {e}"))


@reactive.calc
def raw_data():
    if input.source() == "csv":
        f = input.file()
        if not f: return None
        df = _read_csv_robust(f[0]["datapath"])
        return _coerce(df) if df is not None else None
    if input.source() == "csv_custom":
        return custom_csv_mapped.get()
    if input.source() in ("kobo", "kobo_sync"):          
        # explicit        
        df = kobo_data.get()        
        return _coerce(df.copy()) if (df is not None and not df.empty) else None
    return None

@reactive.calc
def latest_per_facility():
    df = filtered_data()
    if df is None or df.empty or DATE_COL not in df.columns:
        return pd.DataFrame()
    return df.sort_values(DATE_COL).groupby(FACILITY_COL).tail(1)
    
def _set_single(input_id, df, col, parents):
    """Populate a single-select cascading filter, defaulting to All."""
    if df is None or col not in df.columns:
        ui.update_selectize(input_id, choices={ALL_OPTION: t("all_option")},
                            selected=ALL_OPTION)
        return None
    sub = _apply_cascade(df, parents)
    vals = sorted(sub[col].dropna().astype(str).unique().tolist())
    ui.update_selectize(input_id,
                        choices={ALL_OPTION: t("all_option"), **{v: v for v in vals}},
                        selected=ALL_OPTION)


@reactive.effect
def _update_provinces():
    _set_single("province", raw_data(), PROVINCE_COL, [])


@reactive.effect
def _update_districts():
    _set_single("district", raw_data(), DISTRICT_COL,
                [(PROVINCE_COL, "province")])


@reactive.effect
def _update_subdistricts():
    _set_single("subdistrict", raw_data(), SUBDISTRICT_COL,
                [(PROVINCE_COL, "province"), (DISTRICT_COL, "district")])


@reactive.effect
def _update_levels():
    _set_single("level", raw_data(), LEVEL_COL,
                [(PROVINCE_COL, "province"), (DISTRICT_COL, "district"),
                 (SUBDISTRICT_COL, "subdistrict")])


@reactive.effect
def _update_facilities():
    df = raw_data()
    if df is None or FACILITY_COL not in df.columns:
        ui.update_selectize("facilities", choices=[], selected=[])
        ui.update_selectize("detail_facility", choices=[], selected=None)
        return
    df = _apply_cascade(df, CASCADE_LEVELS)
    fac = sorted(df[FACILITY_COL].dropna().astype(str).unique().tolist())
    ui.update_selectize("facilities", choices=fac, selected=fac)
    ui.update_selectize("detail_facility", choices=fac,
                        selected=fac[0] if fac else None)
@reactive.calc
def filtered_data():
    df = raw_data()
    if df is None: return None

    # Global date cutoff: keep assessments on/after the selected date
    sd = input.start_date()
    if sd is not None and DATE_COL in df.columns:
        df = df[df[DATE_COL] >= pd.Timestamp(sd)]
    
    # Province → District → Subdistrict → Level
    df = _apply_cascade(df, CASCADE_LEVELS)

    sel = input.facilities()
    if sel and FACILITY_COL in df.columns:
        df = df[df[FACILITY_COL].astype(str).isin(sel)]

    if input.use_custom_baseline():
        return add_time_anchors(
            df,
            baseline_date=input.baseline_date(),
            buffer_weeks=input.baseline_buffer_weeks(),
        )
    return add_time_anchors(df)

_baseline_initialized = reactive.value(False)

@reactive.effect
def _init_baseline_date():
    if _baseline_initialized.get():
        return
    df = raw_data()
    if df is None or df.empty or DATE_COL not in df.columns:
        return
    earliest = df[DATE_COL].dropna().min()
    if pd.notna(earliest):
        ui.update_date("baseline_date", value=earliest.date())
        _baseline_initialized.set(True)

#Start Date reactive effect
_start_date_initialized = reactive.value(False)

@reactive.effect
def _init_start_date():
    if _start_date_initialized.get():
        return
    df = raw_data()
    if df is None or df.empty or DATE_COL not in df.columns:
        return
    earliest = df[DATE_COL].dropna().min()
    if pd.notna(earliest):
        ui.update_date("start_date", value=earliest.date())
        _start_date_initialized.set(True)

@reactive.effect
def _update_assessments():
    df = filtered_data()
    fac = input.detail_facility()
    if df is None or df.empty or not fac or FACILITY_COL not in df.columns:
        ui.update_selectize("detail_assessment", choices=[], selected=None)
        return
    sub = (
        df[df[FACILITY_COL].astype(str) == str(fac)]
        .dropna(subset=[DATE_COL])
        .sort_values(DATE_COL)
        .reset_index(drop=True)
    )
    if sub.empty:
        ui.update_selectize("detail_assessment", choices=[], selected=None)
        return
    choices = {
        str(i): t("assessment_n_date", n=i+1, date=row[DATE_COL].strftime('%Y-%m-%d'))
        for i, row in sub.iterrows()
    }
    most_recent = str(len(sub) - 1)
    ui.update_selectize("detail_assessment", choices=choices, selected=most_recent)

@reactive.effect
@reactive.event(input.kobo_sync_load)
async def _load_kobo_sync():
    if not IS_WASM:
        kobo_sync_msg.set(("err",
            "Auto-synced data is only available in the deployed browser version. "
            "Use CSV upload for local development."))
        return
    part = input.sync_partition()
    pw   = (input.sync_passphrase() or "").strip()
    if not pw:
        kobo_sync_msg.set(("err", "Enter the access passphrase for your level."))
        return

    kobo_sync_msg.set(("info", "⏳ Loading and decrypting…"))
    try:
        import io
        blob, from_cache = await _fetch_partition_bytes(
            f"{SYNC_BASE_URL}/{part}.enc")
        text = _decrypt_partition(blob, pw)

        df = None
        for sep in [",", ";", "\t"]:
            try:
                tmp = pd.read_csv(io.StringIO(text), sep=sep)
                if tmp.shape[1] > 1:
                    df = tmp
                    break
            except Exception:
                continue
        if df is None or df.empty:
            raise Exception("Decrypted file is empty or unreadable.")

        kobo_data.set(df)   # raw_data() applies _coerce
        if from_cache:
            kobo_sync_msg.set(("info",
                f"📴 Offline — loaded cached data. {len(df):,} records. "
                "Reconnect to refresh."))
        else:
            kobo_sync_msg.set(("ok", f"✅ Loaded {len(df):,} records ({part})."))

    except Exception as e:
        msg = str(e)
        if "WRONG_PASSPHRASE" in msg:
            kobo_sync_msg.set(("err", "❌ Incorrect passphrase for this access level."))
        elif "OFFLINE_NO_CACHE" in msg:
            kobo_sync_msg.set(("err",
                "📴 You're offline and no cached data exists on this device. "
                "Connect once to download your partition."))
        else:
            kobo_sync_msg.set(("err", f"Error: {msg}"))
        kobo_data.set(None)


# ----- Reactive effect: re-translate all input labels & choices on language change
@reactive.effect
def _retranslate_inputs():
    _ = input.language()  # take dependency
    cl = component_labels()
    try:
        ui.update_radio_buttons("source", choices={
            "csv":        t("csv_standard"),
            "csv_custom": t("csv_custom"),
            "kobo_sync":  t("kobo_sync"),
            "kobo":       t("kobo_api"),
        })
    except Exception: pass
    
    try: ui.update_select("sync_partition", 
    label=t("sync_partition"))    
    except Exception: pass    
    try: ui.update_text("sync_passphrase", 
    label=t("sync_passphrase"))    
    except Exception: pass    
    try: ui.update_action_button("kobo_sync_load", 
    label=t("sync_load"))    
    except Exception: pass
    try:
        ui.update_radio_buttons("x_axis", label=t("time_axis"), choices={
            "date": t("reporting_date"),
            "days": t("days_since_baseline"),
            "num":  t("assessment_num"),
        })
    except Exception: pass

    for input_id, key in [
        ("facilities", "facilities"),
        ("components", "components"),
        ("critical_components", "critical_components"),
        ("detail_facility", "facility_inspect"),
        ("detail_assessment", "specific_assessment"),
        ("province", "province"),
        ("district", "district"),          # NEW
        ("subdistrict", "subdistrict"),
        ("level", "level"),
    ]:
        try: ui.update_selectize(input_id, label=t(key))
        except Exception: pass

    try: ui.update_select("language", label=t("language_label"))
    except Exception: pass

    for input_id, key in [
        ("kobo_url", "kobo_url"),
        ("kobo_asset", "asset_uid"),
        ("kobo_token", "api_token"),
    ]:
        try: ui.update_text(input_id, label=t(key))
        except Exception: pass
    
    try:
        ui.update_radio_buttons(
            "trend_filter",
            label=t("trend_filter_label"),
            choices={"all": t("trend_all"), "up": t("trend_up"),
                     "down": t("trend_down"), "flat": t("trend_flat")},
            selected=input.trend_filter(),
        )
    except Exception: pass

    try: ui.update_action_button("kobo_fetch", label=t("fetch_data"))
    except Exception: pass
    try: ui.update_action_button("apply_mapping", label=t("apply_mapping"))
    except Exception: pass
    # Checkbox
    try: ui.update_checkbox("use_custom_baseline", label=t("use_custom_baseline"))
    except Exception: pass
    
    # Date input
    try: ui.update_date("baseline_date", label=t("baseline_date_label"))
    except Exception: pass

    try: ui.update_date("start_date", label=t("start_date_label"))
    except Exception: pass
    
    # Slider
    try: ui.update_slider("baseline_buffer_weeks", label=t("buffer_weeks_label"))
    except Exception: pass

    #Critical Component Translate
    try:
        ui.update_selectize(
            "critical_components",
            choices={c: cl[c] for c in COMPONENT_COLS},
            selected=list(input.critical_components() or []),
        )
    except Exception: pass


# =====================================================================
#                              UI / PAGE
# =====================================================================
ui.page_opts(title="IPC RAT Analysis Dashboard", fillable=False)
#ui.page_opts(title="IPC RAT Dashboard", theme=shinyswatch.theme.cosmo)

ui.tags.script(src="https://cdn.jsdelivr.net/npm/pptxgenjs@3.12.0/dist/pptxgen.bundle.js")

ui.tags.script("""
(function() {
    async function ensurePlotly() {
    if (typeof window.Plotly !== 'undefined' && window.Plotly.toImage) {
        return window.Plotly;
    }
    if (window.__plotlyLoadingPromise) {
        return window.__plotlyLoadingPromise;
    }
    window.__plotlyLoadingPromise = new Promise((resolve, reject) => {
        const s = document.createElement('script');
        s.src = 'https://cdn.plot.ly/plotly-2.35.2.min.js';
        s.async = true;
        s.onload  = () => resolve(window.Plotly);
        s.onerror = () => reject(new Error('Could not load Plotly.js from CDN'));
        document.head.appendChild(s);
    });
    return window.__plotlyLoadingPromise;
    }

  function getActiveTabPane() {
    // Bootstrap 5 active tab content
    return document.querySelector(
      '.tab-content > .tab-pane.show.active, .tab-content > .tab-pane.active'
    );
  }

  function getCardTitle(chartEl) {
    const card = chartEl.closest('.card');
    if (!card) return 'Chart';
    const header = card.querySelector('.card-header');
    return header ? header.textContent.trim() : 'Chart';
  }

  function timestamp() {
    const d = new Date();
    return d.toISOString().slice(0, 10);
  }

  // -------- PPTX EXPORT --------
  window.exportTabToPPTX = async function(tabLabel) {
    if (typeof PptxGenJS === 'undefined') {
      alert('Export library still loading — please try again in a moment.');
      return;
    }
    const pane = getActiveTabPane();
    if (!pane) return;

    const charts = pane.querySelectorAll('.js-plotly-plot');
    if (!charts.length) {
      alert('No charts found on this tab.');
      return;
    }

    // Disable the button visually while we work
    const btn = document.activeElement;
    const origText = btn ? btn.textContent : null;
    if (btn) { btn.textContent = '⏳ Building PowerPoint…'; btn.disabled = true; }

    try {
      const Plotly = await ensurePlotly();
      const pres = new PptxGenJS();
      pres.layout = 'LAYOUT_WIDE';   // 13.333 × 7.5 inches
      pres.title  = tabLabel + ' — IPC RAT Analysis';

      // Title slide
      const title = pres.addSlide();
      title.background = { color: '0d6efd' };
      title.addText(tabLabel, {
        x: 0.5, y: 2.5, w: 12.3, h: 1.2,
        fontSize: 44, bold: true, color: 'FFFFFF', align: 'center'
      });
      title.addText('IPC RAT Analysis Dashboard', {
        x: 0.5, y: 3.7, w: 12.3, h: 0.5,
        fontSize: 20, color: 'E7F1FF', align: 'center'
      });
      title.addText('Generated ' + new Date().toLocaleDateString(), {
        x: 0.5, y: 4.3, w: 12.3, h: 0.4,
        fontSize: 14, color: 'E7F1FF', align: 'center'
      });

      // One slide per chart
      for (const chart of charts) {
        const slideTitle = getCardTitle(chart);

        // Get a high-resolution PNG of the chart
        const dataUrl = await Plotly.toImage(chart, {
          format: 'png',
          width:  1600,
          height: 900,
          scale:  2
        });

        const slide = pres.addSlide();
        slide.addText(slideTitle, {
          x: 0.3, y: 0.25, w: 12.7, h: 0.6,
          fontSize: 22, bold: true, color: '0d6efd'
        });
        slide.addImage({
          data: dataUrl,
          x: 0.5, y: 1.0, w: 12.3, h: 6.2
        });
        slide.addText('IPC RAT Dashboard · ' + new Date().toLocaleDateString(), {
          x: 0.3, y: 7.15, w: 12.7, h: 0.3,
          fontSize: 9, italic: true, color: '888888'
        });
      }

      const safeName = tabLabel.replace(/[^\\w\\-]+/g, '_');
      await pres.writeFile({ fileName: `IPC_RAT_${safeName}_${timestamp()}.pptx` });
    } catch (err) {
      console.error(err);
      alert('Export failed: ' + err.message);
    } finally {
      if (btn) { btn.textContent = origText; btn.disabled = false; }
    }
  };

  // -------- CSV EXPORT (for tables) --------
  window.exportTablesToCSV = function(tabLabel) {
    const pane = getActiveTabPane();
    if (!pane) return;

    // Shiny DataGrid renders into <table> elements
    const tables = pane.querySelectorAll('table');
    if (!tables.length) {
      alert('No tables found on this tab.');
      return;
    }

    tables.forEach((tbl, idx) => {
      const rows = [];
      tbl.querySelectorAll('tr').forEach(tr => {
        const cells = Array.from(tr.querySelectorAll('th,td')).map(td => {
          const txt = (td.innerText || '').replace(/\\r?\\n/g, ' ').trim();
          // Escape CSV-special chars
          return /[",\\n]/.test(txt) ? '"' + txt.replace(/"/g, '""') + '"' : txt;
        });
        if (cells.length) rows.push(cells.join(','));
      });
      if (!rows.length) return;

      const card = tbl.closest('.card');
      const header = card ? card.querySelector('.card-header') : null;
      const title = header ? header.textContent.trim() : ('Table_' + (idx + 1));
      const safe = title.replace(/[^\\w\\-]+/g, '_');

      const blob = new Blob([rows.join('\\n')], { type: 'text/csv;charset=utf-8;' });
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href = url;
      a.download = `IPC_RAT_${safe}_${timestamp()}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    });
  };

})();
""")


ui.tags.style("""
/* Don't let card bodies squeeze full-size plots */
.card .html-fill-container > .js-plotly-plot { min-height: 400px; }
details > summary { list-style: none; }
details > summary::-webkit-details-marker { display: none; }
details > summary::before {
    content: '▶'; display:inline-block; margin-right:6px;
    transition: transform .15s ease;
}
details[open] > summary::before { transform: rotate(90deg); }
.kpi-strip { background:white; padding:8px 0; }

.accordion-button { font-weight: 600; transition: background-color .15s ease; }
.accordion-button:hover { background-color: #f0f0f0 !important; }
.accordion-button:not(.collapsed) { background-color: #e7f1ff; color: #0d6efd; }
.accordion-body { padding: 12px 14px; }


/* Make card-header look right when wrapped by @render.ui output div */
.card > .shiny-html-output:first-child > .card-header {
    border-top-left-radius: inherit;
    border-top-right-radius: inherit;
    margin: 0;
}
.card > .shiny-html-output:first-child {
    border-bottom: 1px solid rgba(0,0,0,.125);
}

/* Don't let bslib's flexbox compress Plotly charts below their declared height */
.html-fill-container .js-plotly-plot,
.html-fill-item       .js-plotly-plot {
    flex: 0 0 auto !important;
    min-height: 0 !important;
    height: auto !important;
}

/* And make sure card bodies that hold plots can grow to fit them */
.card .html-fill-container,
.card .html-fill-item {
    overflow: visible !important;
}

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

body { font-family: 'Inter', sans-serif; background: #f5f7fa; }
.card {
    border: none !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.04), 0 4px 12px rgba(0,0,0,.04);
    transition: transform .15s ease, box-shadow .15s ease;
}
.card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,.08); }
.card-header { background: white; border-bottom: 1px solid #f0f2f5; font-weight: 600; }
.value-box { border-radius: 12px !important; }

/* Deep-dive selectors must float above the KPI value boxes below them */
.deep-dive-controls {
    position: relative;
    z-index: 1030;
    overflow: visible !important;
}
.deep-dive-controls .card-body { overflow: visible !important; }
.deep-dive-controls .selectize-dropdown {
    z-index: 2000 !important;
}

/* Critical-component grid: sticky header row + sticky facility column */
.bundle-grid-wrap {
    max-height: 70vh;
    overflow: auto;                 /* scrolls both axes; width fills container */
    border: 1px solid #e9ecef;
    border-radius: 8px;
}
.bundle-grid {
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
    font-size: .78rem;
}
.bundle-grid th, .bundle-grid td {
    padding: 6px 8px;
    text-align: center;
    border-bottom: 2px solid #fff;
    white-space: nowrap;
}
.bundle-grid td { font-weight: 600; }
/* sticky column headers (top) */
.bundle-grid thead th {
    position: sticky; top: 0; z-index: 2;
    background: #2c3e50; color: #fff; font-weight: 600;
    vertical-align: bottom; min-width: 70px;
}
/* sticky facility column (left) */
.bundle-grid tbody th {
    position: sticky; left: 0; z-index: 1;
    background: #fff; text-align: left; font-weight: 600;
    min-width: 100px; box-shadow: 1px 0 0 #e9ecef;
}
/* top-left corner sits above both */
.bundle-grid thead th.corner {
    left: 0; z-index: 4; text-align: left; min-width: 170px;
}

""")


# =====================================================================
#                              SIDEBAR (Accordion)
# =====================================================================
    
with ui.sidebar(width=380, open="open"):

    with ui.accordion(id="sidebar_acc", multiple=True, open=["📂 Data Source"]):

        # ====================== Data Source ======================
        with ui.accordion_panel("📂 Data Source"):

            ui.input_select(
                "language",
                "🌐 Language",
                choices=LANG_CHOICES,
                selected="en",
            )

            ui.input_radio_buttons(
                "source", None,
                {
                    "csv":        "📄 CSV Upload (Standard)",
                    "csv_custom": "🔧 CSV Upload (Custom Mapping)",
                    "kobo_sync":  "🔄 Kobo (Auto-synced)",
                    "kobo":       "🌐 KoboToolbox API",
                },
                selected="csv",
            )

            with ui.panel_conditional("input.source === 'csv'"):
                ui.input_file("file", "Upload CSV File", accept=[".csv"])

            with ui.panel_conditional("input.source === 'csv_custom'"):
                ui.input_file("file_custom", "Upload CSV File", accept=[".csv"])

                @render.ui
                def custom_mapping_ui():
                    df = custom_csv_raw.get()
                    if df is None:
                        return ui.div(
                            ui.tags.small(t("upload_to_begin"), class_="text-muted"),
                            class_="alert alert-light p-2 mt-2",
                        )
                    cols = list(df.columns)
                    choices = [NONE_OPTION] + cols
                    required_inputs, total_inputs, component_inputs = [], [], []
                    for target_key, label in MAP_TARGETS:
                        widget = ui.input_selectize(
                            f"map__{target_key}", label,
                            choices=choices, selected=best_match(target_key, cols),
                        )
                        if target_key in (FACILITY_COL, FACILITY_OTHER_COL, DATE_COL):
                            required_inputs.append(widget)
                        elif target_key == SCORE_TOTAL:
                            total_inputs.append(widget)
                        else:
                            component_inputs.append(widget)
                    return ui.div(
                        ui.tags.small(t("columns_detected", n=len(cols)),
                                      class_="text-success"),
                        details_panel(t("required_fields"),    *required_inputs,  open=True),
                        details_panel(t("total_score_section"),*total_inputs,     open=False),
                        details_panel(t("component_scores"),   *component_inputs, open=False),
                        ui.input_action_button(
                            "apply_mapping", t("apply_mapping"),
                            class_="btn-success w-100 mt-3",
                        ),
                        class_="mt-2",
                    )

                @render.ui
                def mapping_status():
                    msg = mapping_status_msg.get()
                    if not msg: return None
                    cls = {"ok":"success","err":"danger","info":"info"}.get(msg[0], "info")
                    return ui.div(msg[1], class_=f"alert alert-{cls} mt-2 p-2 small")

            with ui.panel_conditional("input.source === 'kobo'"):
                ui.input_text("kobo_url", "Kobo Server URL", value="https://kf.kobotoolbox.org")
                ui.input_text("kobo_asset", "Asset UID")
                ui.input_password("kobo_token", "API Token")
                ui.input_action_button("kobo_fetch", "🚀 Fetch Data",
                                       class_="btn-primary w-100")
                
                ui.input_action_button(                
                    "kobo_cors_check", "🔍 Test Connection",                
                    class_="btn-outline-secondary btn-sm w-100 mb-2",            
                    )            
                
                @render.ui            
                def kobo_cors_result():                
                    msg = kobo_cors_msg.get()                
                    if not msg: return None                
                    cls = {"ok":"success","err":"danger","info":"info"}.get(msg[0],"info")                
                    return ui.div(msg[1], class_=f"alert alert-{cls} mt-1 p-2 small")

                @render.ui
                def kobo_status():
                    msg = kobo_status_msg.get()
                    if not msg: return None
                    cls = {"ok":"success","err":"danger","info":"info"}.get(msg[0], "info")
                    return ui.div(msg[1], class_=f"alert alert-{cls} mt-2 p-2 small")

            with ui.panel_conditional("input.source === 'kobo_sync'"):
                ui.input_select("sync_partition", "🗺️ Data Access Level",
                                SYNC_PARTITIONS)
                ui.input_password("sync_passphrase", "🔑 Access Passphrase")
                ui.input_action_button("kobo_sync_load", "📥 Load Data",
                                       class_="btn-primary w-100 mt-2")

                @render.ui
                def kobo_sync_status():
                    msg = kobo_sync_msg.get()
                    if not msg: return None
                    cls = {"ok":"success","err":"danger","info":"info"}.get(msg[0], "info")
                    return ui.div(ui.HTML(msg[1]),
                                  class_=f"alert alert-{cls} mt-2 p-2 small")

                @render.ui
                def kobo_sync_note():
                    return ui.tags.small(t("sync_note"),
                                         class_="text-muted d-block mt-2",
                                         style="font-size:.78rem;")

        # ====================== View Controls ======================
        with ui.accordion_panel("🔍 View Controls"):

            ui.input_radio_buttons(
                "x_axis", "Time Axis",
                {"date": "Reporting Date",
                 "days": "Days Since Baseline",
                 "num":  "Assessment #"},
                selected="days",
            )
            
            ui.input_date("start_date", "📅 Include data on/after", value=None)

            # NEW: geographic filters (default to all)
            ui.input_selectize("province",    "🗺️ Province",       choices=[], multiple=False)
            ui.input_selectize("district",    "🗺️ District",       choices=[], multiple=False)
            ui.input_selectize("subdistrict", "🗺️ Subdistrict",    choices=[], multiple=False)
            ui.input_selectize("level",       "🏷️ Facility Level", choices=[], multiple=False)
            ui.input_selectize("facilities",  "Facilities",        choices=[], multiple=True)


            ui.hr()

            ui.input_checkbox(
                "use_custom_baseline",
                "Use custom baseline anchor",
                value=False,
            )
            
            with ui.panel_conditional("input.use_custom_baseline"):
                ui.input_date(
                    "baseline_date",
                    "Baseline Date",
                    value=None,            # auto-filled from data (see Step 5)
                )
                ui.input_slider(
                    "baseline_buffer_weeks",
                    "Buffer (± weeks)",
                    min=0, max=26, value=4, step=1,
                )

        # ====================== Outbreak Settings ======================
        with ui.accordion_panel("🚨 Outbreak Settings"):

            @render.ui
            def thresholds_info_ui():
                return ui.tags.small(t("thresholds_info"),
                                     class_="text-muted d-block mb-2")

            DEFAULT_CRITICAL = [
                "score_s1",
                "score_s2",
                "score_s3",   # Hand Hygiene
                "score_s4",   # Screening
                "score_s5",   # Isolation
                "score_s6",   # PPE
                "score_s7",
                "score_s8",   # Env. Cleaning
                "score_s9",   # Decontamination
                "score_s10",
                "score_s11",
                "score_s12",  # Patient Placement
                "score_s13",
                "score_s14",
                "score_s15",
                "score_s16",
                "score_s17",  # Dead Body Management
            ]
            ui.input_selectize(
                "critical_components",
                "Outbreak-Critical Components",
                choices={c: COMPONENT_LABELS[c] for c in COMPONENT_COLS},
                selected=DEFAULT_CRITICAL,
                multiple=True,
            )


# =====================================================================
#                          MAIN: TABS
# =====================================================================
with ui.navset_card_tab(id="main_tabs"):

    # =================================================================
    #                  🚨 Outbreak Response TAB
    # =================================================================
    with ui.nav_panel("🚨 Outbreak Response"):

        @render.ui
        def banner_outbreak():
            return section_banner("🚨", t("outbreak_title"),
                                  t("outbreak_subtitle"), color="#dc3545")
        
        # ---- Export toolbar (PowerPoint + CSV) ----
        ui.HTML("""
        <div style="display:flex; gap:8px; justify-content:flex-end;
                    margin: -8px 0 12px 0;">
          <button type="button" class="btn btn-outline-primary btn-sm"
                  onclick="exportTabToPPTX('Outbreak Response')">
            📥 Export visuals to PowerPoint
          </button>
          <button type="button" class="btn btn-outline-secondary btn-sm"
                  onclick="exportTablesToCSV('Outbreak Response')">
            📊 Export tables to CSV
          </button>
        </div>
        """)

        # ----- KPI strip -----
        with ui.layout_columns(col_widths=[4, 4, 4], fill=False):

            with ui.value_box(showcase=ui.HTML("🟢"), theme="bg-gradient-teal-green"):
                @render.text
                def lbl_kpi_ready(): return t("kpi_ready")
                @render.text
                def kpi_ready():
                    d = latest_per_facility()
                    if d.empty or SCORE_TOTAL not in d.columns: return "—"
                    s = d[SCORE_TOTAL].dropna()
                    if s.empty: return "—"
                    return f"{int((s >= READY_THRESHOLD).sum())} / {len(s)}"

            with ui.value_box(showcase=ui.HTML("🟡"), theme="bg-gradient-orange-red"):
                @render.text
                def lbl_kpi_at_risk(): return t("kpi_at_risk")
                @render.text
                def kpi_at_risk():
                    d = latest_per_facility()
                    if d.empty or SCORE_TOTAL not in d.columns: return "—"
                    s = d[SCORE_TOTAL].dropna()
                    if s.empty: return "—"
                    n = int(((s > CRITICAL_THRESHOLD) & (s < READY_THRESHOLD)).sum())
                    return f"{n} / {len(s)}"

            with ui.value_box(showcase=ui.HTML("🔴"), theme="bg-gradient-red-orange"):
                @render.text
                def lbl_kpi_critical(): return t("kpi_critical")
                @render.text
                def kpi_critical():
                    d = latest_per_facility()
                    if d.empty or SCORE_TOTAL not in d.columns: return "—"
                    s = d[SCORE_TOTAL].dropna()
                    if s.empty: return "—"
                    return f"{int((s <= CRITICAL_THRESHOLD).sum())} / {len(s)}"

        # ----- Outbreak Readiness Index -----
        with ui.card(full_screen=True):
            @render.ui
            def h_readiness_index():
                return ui.card_header(t("card_readiness_index"))

            @render.ui
            def desc_readiness_index():
                return ui.tags.small(t("desc_readiness_index"),
                                     class_="text-muted px-3")

            @render_plotly
            def plot_readiness_index():
                df = filtered_data()
                if df is None or df.empty or SCORE_TOTAL not in df.columns:
                    return go.Figure()
                latest = df.sort_values(DATE_COL).groupby(FACILITY_COL).tail(1)
                d = latest[[FACILITY_COL, SCORE_TOTAL]].dropna(subset=[SCORE_TOTAL])
                if d.empty:
                    return go.Figure()
                d = d.sort_values(SCORE_TOTAL, ascending=False)

                def _band_color(s):
                    if s <= CRITICAL_THRESHOLD: return COLOR_CRITICAL
                    if s < READY_THRESHOLD:     return COLOR_AT_RISK
                    return COLOR_READY
                def _band_emoji(s):
                    if s <= CRITICAL_THRESHOLD: return "🔴"
                    if s < READY_THRESHOLD:     return "🟡"
                    return "🟢"

                fig = go.Figure(go.Bar(
                    x=d[SCORE_TOTAL], y=d[FACILITY_COL], orientation="h",
                    marker=dict(color=[_band_color(s) for s in d[SCORE_TOTAL]],
                                line=dict(color="white", width=1)),
                    text=[f"{s:.0f} {_band_emoji(s)}" for s in d[SCORE_TOTAL]],
                    textposition="outside", cliponaxis=False,
                    hovertemplate="<b>%{y}</b><br>" + t("chart_total_score")
                                  + ": %{x:.1f}<extra></extra>",
                ))
                fig.add_vline(x=CRITICAL_THRESHOLD, line_dash="dash", line_color=COLOR_CRITICAL,
                              annotation_text=t("chart_critical_thresh"),
                              annotation_position="top right",
                              annotation_font_color=COLOR_CRITICAL)
                fig.add_vline(x=READY_THRESHOLD, line_dash="dash", line_color=COLOR_READY,
                              annotation_text=t("chart_ready_thresh"),
                              annotation_position="top right",
                              annotation_font_color=COLOR_READY)
                fig.update_layout(
                    height=max(420, len(d) * 30 + 100),
                    xaxis=dict(title=t("chart_total_score"), range=[0, 110], gridcolor="#eee"),
                    yaxis=dict(tickmode="array", tickvals=list(range(len(d))),
                               ticktext=d[FACILITY_COL].tolist()),
                    yaxis_title="", plot_bgcolor="white",
                    margin=dict(l=10, r=20, t=30, b=10),
                )
                return fig
        # ----- Critical Bundle Compliance Grid -----
        with ui.card(full_screen=True, min_height="650px"):
            @render.ui
            def h_bundle_grid():
                return ui.card_header(t("card_bundle_grid"))

            @render.ui
            def desc_bundle_grid():
                return ui.tags.small(t("desc_bundle_grid"),
                                     class_="text-muted px-3")
            @render.ui
            def bundle_grid():
                df = filtered_data()
                if df is None or df.empty:
                    return ui.div(class_="text-muted p-3")
                critical = _ordered_critical(df)
                if not critical:
                    return ui.div(class_="text-muted p-3")

                latest = (df.sort_values(DATE_COL).groupby(FACILITY_COL).tail(1)
                            .set_index(FACILITY_COL)[critical].astype(float))
                # worst-first by number of components below ready
                order = (latest < READY_THRESHOLD).sum(axis=1).sort_values(ascending=False).index
                latest = latest.loc[order]
                cl = component_labels()

                def cell_color(v):
                    if pd.isna(v):                 return "#e9ecef"
                    if v <= CRITICAL_THRESHOLD:    return COLOR_CRITICAL
                    if v < READY_THRESHOLD:        return COLOR_AT_RISK
                    return COLOR_READY

                header = ui.tags.tr(
                    ui.tags.th(t("col_facility"), class_="corner"),
                    *[ui.tags.th(cl.get(c, c)) for c in latest.columns],
                )
                body_rows = []
                for fac, row in latest.iterrows():
                    cells = [ui.tags.th(str(fac), scope="row")]
                    for v in row:
                        txt = "—" if pd.isna(v) else f"{v:.0f}"
                        color = "#6c757d" if pd.isna(v) else "#fff"
                        cells.append(ui.tags.td(
                            txt, style=f"background:{cell_color(v)};color:{color};"))
                    body_rows.append(ui.tags.tr(*cells))

                return ui.div(
                    ui.tags.table(
                        ui.tags.thead(header),
                        ui.tags.tbody(*body_rows),
                        class_="bundle-grid",
                    ),
                    class_="bundle-grid-wrap",
                )
        # ----- Geo Map -----
        with ui.card(full_screen=True):
            @render.ui
            def h_facility_map():
                return ui.card_header(t("card_facility_map"))

            @render.ui
            def desc_facility_map():
                return ui.tags.small(t("desc_facility_map"),
                                     class_="text-muted px-3")

            @render_plotly
            def plot_facility_map():
                df = filtered_data()
                if df is None or df.empty:
                    return _map_placeholder(t("map_no_data"))

                if LATITUDE_COL not in df.columns or LONGITUDE_COL not in df.columns:
                    return _map_placeholder(
                        t("map_no_coords") + "<br><br>"
                        f"<b>{LATITUDE_COL}</b> / <b>{LONGITUDE_COL}</b>"
                    )

                critical = _ordered_critical(df)
                if not critical:
                    return _map_placeholder(t("map_no_critical"))

                latest = df.sort_values(DATE_COL).groupby(FACILITY_COL).tail(1).copy()
                latest["Readiness"] = latest[critical].astype(float).mean(axis=1)
                latest = latest.dropna(subset=[LATITUDE_COL, LONGITUDE_COL, "Readiness"])
                latest = latest[
                    latest[LATITUDE_COL].between(-90, 90) &
                    latest[LONGITUDE_COL].between(-180, 180) &
                    ~((latest[LATITUDE_COL] == 0) & (latest[LONGITUDE_COL] == 0))
                ]

                if latest.empty:
                    return _map_placeholder(t("map_no_valid"))

                ready_lbl    = t("status_ready_short")
                at_risk_lbl  = t("status_at_risk_short")
                critical_lbl = t("status_critical_short")

                def band(s):
                    if s <= CRITICAL_THRESHOLD: return critical_lbl
                    if s < READY_THRESHOLD:     return at_risk_lbl
                    return ready_lbl
                latest["Status"] = latest["Readiness"].apply(band)
                latest["Last Assessed"] = latest[DATE_COL].dt.date.astype(str)

                fig = px.scatter_mapbox(
                    latest,
                    lat=LATITUDE_COL, lon=LONGITUDE_COL,
                    color="Status", size='Readiness', size_max=22,
                    hover_name=FACILITY_COL,
                    hover_data={
                        "Readiness": ":.1f",
                        "Last Assessed": True, "Status": True,
                        LATITUDE_COL: False, LONGITUDE_COL: False,
                    },
                    color_discrete_map={
                        ready_lbl: COLOR_READY,
                        at_risk_lbl: COLOR_AT_RISK,
                        critical_lbl: COLOR_CRITICAL,
                    },
                    zoom=5,
                )
                fig.update_layout(
                    mapbox_style="open-street-map",
                    mapbox=dict(
                        center=dict(
                            lat=float(latest[LATITUDE_COL].mean()),
                            lon=float(latest[LONGITUDE_COL].mean()),
                        ),
                    ),
                    height=600,
                    margin=dict(l=0, r=0, t=10, b=10),
                    legend=dict(orientation="h", yanchor="top", y=1.0,
                                xanchor="left", x=0.0),
                )
                return fig

        # ----- Dispatch Decision Table -----
        with ui.card(full_screen=True):
            @render.ui
            def h_dispatch():
                return ui.card_header(t("card_dispatch"))

            @render.ui
            def desc_dispatch():
                return ui.tags.small(t("desc_dispatch"),
                                     class_="text-muted px-3")

            @render.data_frame
            def dispatch_table():
                r = outbreak_readiness(filtered_data(), input.critical_components())
                if r.empty: return pd.DataFrame()
                r = r.copy()
                r["Status"] = r["Status"].map(_translate_status)
                r = r.rename(columns={
                    "Facility":          t("col_facility"),
                    "Readiness":         t("col_readiness"),
                    "Critical Gaps":     t("col_critical_gaps"),
                    "Last Assessed":     t("col_last_assessed"),
                    "Status":            t("col_status"),
                })
                return render.DataGrid(r, filters=True, height="450px")


    # =================================================================
    #                       🌐 Summary VIEW TAB
    # =================================================================
    with ui.nav_panel("🌐 Summary View"):

        @render.ui
        def banner_network():
            return section_banner("🌐", t("network_title"),
                                  t("network_subtitle"), color="#0d6efd")

        # ---- Export toolbar (PowerPoint + CSV) ----
        ui.HTML("""
        <div style="display:flex; gap:8px; justify-content:flex-end;
                    margin: -8px 0 12px 0;">
          <button type="button" class="btn btn-outline-primary btn-sm"
                  onclick="exportTabToPPTX('Summary View')">
            📥 Export visuals to PowerPoint
          </button>
          <button type="button" class="btn btn-outline-secondary btn-sm"
                  onclick="exportTablesToCSV('Summary View')">
            📊 Export tables to CSV
          </button>
        </div>
        """)
        
        # ----- KPI strip -----
        with ui.div(class_="kpi-strip"):
            with ui.layout_columns(col_widths=[3, 3, 3, 3], fill=False):

                with ui.value_box(showcase=ui.HTML("🏥"), theme="primary"):
                    @render.text
                    def lbl_kpi_n_facilities(): return t("kpi_facilities_tracked")
                    @render.text
                    def kpi_n_facilities():
                        df = filtered_data()
                        return "—" if df is None or df.empty else f"{df[FACILITY_COL].nunique():,}"

                with ui.value_box(showcase=ui.HTML("🔁"),
                                  theme="bg-gradient-indigo-purple"):
                    @render.text
                    def lbl_kpi_avg_n(): return t("kpi_avg_assessments")
                    @render.text
                    def kpi_avg_n():
                        df = filtered_data()
                        if df is None or df.empty: return "—"
                        return f"{df.groupby(FACILITY_COL).size().mean():.1f}"

                with ui.value_box(showcase=ui.HTML("📈"),
                                  theme="bg-gradient-teal-green"):
                    @render.text
                    def lbl_kpi_delta(): return t("kpi_median_delta")
                    @render.text
                    def kpi_delta_total():
                        df = filtered_data()
                        if df is None or df.empty or SCORE_TOTAL not in df.columns: return "—"
                        _, _, delta = first_last_per_facility(df, [SCORE_TOTAL])
                        v = delta[SCORE_TOTAL].median()
                        return "—" if pd.isna(v) else f"{v:+.1f}"

                with ui.value_box(showcase=ui.HTML("📅"),
                                  theme="bg-gradient-blue-cyan"):
                    @render.text
                    def lbl_kpi_followup(): return t("kpi_median_followup")
                    @render.text
                    def kpi_followup():
                        df = filtered_data()
                        if df is None or df.empty: return "—"
                        span = df.groupby(FACILITY_COL)["Days Since Baseline"].max()
                        return f"{span.median():.0f}"
                        
        with ui.layout_columns(col_widths=[4, 4, 4], fill=False):
        
                with ui.value_box(showcase=ui.HTML("📊"), theme="bg-gradient-yellow-orange"):
                    @render.text
                    def lbl_kpi_total_assessments(): return t("kpi_total_assessments")
                    @render.text
                    def kpi_total_assessments():
                        df = filtered_data()
                        if df is None or df.empty: return "—"
                        return f"{len(df):,}"
        
                with ui.value_box(showcase=ui.HTML("🗓️"), theme="bg-gradient-blue-cyan"):
                    @render.text
                    def lbl_kpi_total_30d(): return t("kpi_total_30d")
                    @render.text
                    def kpi_total_30d():
                        df = filtered_data()
                        if df is None or df.empty or DATE_COL not in df.columns: return "—"
                        cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(days=30)
                        return f"{int((df[DATE_COL] >= cutoff).sum()):,}"
        
                with ui.value_box(showcase=ui.HTML("🕐"), theme="bg-gradient-purple-pink"):
                    @render.text
                    def lbl_kpi_total_7d(): return t("kpi_total_7d")
                    @render.text
                    def kpi_total_7d():
                        df = filtered_data()
                        if df is None or df.empty or DATE_COL not in df.columns: return "—"
                        cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(days=7)
                        return f"{int((df[DATE_COL] >= cutoff).sum()):,}"
        
        # ----- Total Score Trajectory -----
        with ui.card(full_screen=True):
            @render.ui
            def h_total_traj():
                return ui.card_header(t("card_total_traj"))
        

            @render.ui
            def desc_total_traj():
                return ui.tags.small(t("desc_total_traj"),
                                     class_="text-muted px-3")

            ui.input_radio_buttons(            
                "trend_filter", None,
                {"all": "All", "up": "📈 Increasing",
                 "down": "📉 Decreasing", "flat": "➡️ Static"},
                selected="all", inline=True,
            )

            @render_plotly
            def plot_total_trajectory():
                df = filtered_data()
                if df is None or df.empty or SCORE_TOTAL not in df.columns:
                    return go.Figure()
                
                # ---- Trend filter (first → last total score change) ----
                tf = input.trend_filter()
                if tf and tf != "all":
                    _, _, delta = first_last_per_facility(df, [SCORE_TOTAL])
                    d = delta[SCORE_TOTAL]
                    if tf == "up":
                        keep = d[d >= 3].index
                    elif tf == "down":
                        keep = d[d <= -3].index
                    else:  # flat / static
                        keep = d[(d > -3) & (d < 3)].index
                    df = df[df[FACILITY_COL].isin(keep)]
                    if df.empty:
                        return go.Figure()
                
                x_col, x_lbl = x_axis_map()[input.x_axis()]
                d = df.dropna(subset=[SCORE_TOTAL, x_col])
                fig = px.line(
                    d, x=x_col, y=SCORE_TOTAL, color=FACILITY_COL,
                    markers=True,
                    labels={SCORE_TOTAL: t("chart_total_score"),
                            x_col: x_lbl, FACILITY_COL: t("col_facility")},
                )
                fig.add_hline(y=CRITICAL_THRESHOLD, line_dash="dash",
                              line_color=COLOR_CRITICAL,
                              annotation_text=t("chart_critical_thresh"),
                              annotation_position="bottom right",
                              annotation_font_color=COLOR_CRITICAL)
                fig.add_hline(y=READY_THRESHOLD, line_dash="dash",
                              line_color=COLOR_READY,
                              annotation_text=t("chart_ready_thresh"),
                              annotation_position="top right",
                              annotation_font_color=COLOR_READY)
                if input.x_axis() in ("days", "num"):
                    fig.add_vline(x=0 if input.x_axis()=="days" else 1,
                                  line_dash="dot", line_color="gray",
                                  annotation_text=t("chart_baseline"),
                                  annotation_position="top")
                fig.update_layout(margin=dict(l=10,r=10,t=30,b=10), height=480,
                                  legend_title=t("col_facility"),
                                  hovermode="x unified")
                return fig

        # ----- Change from Baseline Heatmap -----
        with ui.card(full_screen=True):
            @render.ui
            def h_delta_heatmap():
                return ui.card_header(t("card_delta_heatmap"))

            @render_plotly
            def plot_delta_heatmap():
                df = filtered_data()
                labels = component_labels()
                if df is None or df.empty: return go.Figure()
                cols = [c for c in COMPONENT_COLS if c in df.columns]
                if not cols: return go.Figure()
                _, _, delta = first_last_per_facility(df, cols)
                delta.columns = [labels.get(c, c) for c in delta.columns]
                vmax = max(abs(float(delta.values.min())), abs(float(delta.values.max())), 1)
                fig = px.imshow(delta, color_continuous_scale="RdYlGn",
                                zmin=-vmax, zmax=vmax, aspect="auto",
                                labels=dict(color="Δ " + t("col_score")), text_auto=".0f")
                fig.update_layout(
                    margin=dict(l=10, r=10, t=50, b=10),     # was t=30 — bumped for the new colorbar
                    height=max(400, len(delta) * 28 + 150),  # was +150
                    xaxis_title="", yaxis_title="",
                    coloraxis_colorbar=dict(                 # NEW
                        orientation="h",
                        thickness=14,
                        len=0.55,                            # fixed at 55% of plot width
                        xanchor="center", x=0.5,
                        yanchor="bottom", y=1.02,            # sits just above the heatmap
                    ),
                )
                fig.update_xaxes(tickangle=-45)
                return fig

        # ----- Facility Progress Summary Table -----
        with ui.card(full_screen=True):
            @render.ui
            def h_summary():
                return ui.card_header(t("card_summary"))

            @render.data_frame
            def facility_summary():
                df = filtered_data()
                if df is None or df.empty: return pd.DataFrame()
                df = df.sort_values(DATE_COL)
                g = df.groupby(FACILITY_COL)
                out = pd.DataFrame({
                    t("col_facility"):      g.size().index,
                    t("col_assessments"):   g.size().values,
                    t("col_baseline_date"): g[DATE_COL].min().dt.date.values,
                    t("col_latest_date"):   g[DATE_COL].max().dt.date.values,
                    t("col_followup_days"): (g[DATE_COL].max() - g[DATE_COL].min()).dt.days.values,
                })
                if SCORE_TOTAL in df.columns:
                    first = g[SCORE_TOTAL].first().values
                    last  = g[SCORE_TOTAL].last().values
                    out[t("col_baseline_total")] = pd.Series(first).round(1).values
                    out[t("col_latest_total")]   = pd.Series(last).round(1).values
                    out[t("col_delta_total")]    = (pd.Series(last) - pd.Series(first)).round(1).values

                    def _status(v):
                        if pd.isna(v): return "—"
                        if v <= CRITICAL_THRESHOLD: return t("status_critical_short")
                        if v < READY_THRESHOLD:    return t("status_at_risk_short")
                        return t("status_ready_short")
                    out[t("col_latest_status")] = [_status(v) for v in out[t("col_latest_total")]]

                return render.DataGrid(out, filters=True, height="450px")


    # =================================================================
    #                  🏥 FACILITY DEEP DIVE TAB
    # =================================================================
    with ui.nav_panel("🏥 Facility Deep Dive"):

        @render.ui
        def banner_deep_dive():
            return section_banner("🏥", t("deep_dive_title"),
                                  t("deep_dive_subtitle"), color="#198754")
        
        # ---- Export toolbar (PowerPoint + CSV) ----
        ui.HTML("""
        <div style="display:flex; gap:8px; justify-content:flex-end;
                    margin: -8px 0 12px 0;">
          <button type="button" class="btn btn-outline-primary btn-sm"
                  onclick="exportTabToPPTX('Facility Deep Dive')">
            📥 Export visuals to PowerPoint
          </button>
          <button type="button" class="btn btn-outline-secondary btn-sm"
                  onclick="exportTablesToCSV('Facility Deep Dive')">
            📊 Export tables to CSV
          </button>
        </div>
        """)

        with ui.card(class_="mb-3 deep-dive-controls",
                     style="background:#f3faf5; border-left:4px solid #198754;"):
            with ui.layout_columns(col_widths=[6, 6]):
                ui.input_selectize("detail_facility", "🏥 Facility to Inspect",
                                   choices=[], multiple=False)
                ui.input_selectize("detail_assessment",
                                   "📋 Specific Assessment (defaults to most recent)",
                                   choices=[], multiple=False)
        # ---- KPI strip: assessment activity for the selected facility ----
        with ui.layout_columns(col_widths=[4, 4, 4], fill=False):
        
            with ui.value_box(showcase=ui.HTML("📋"), theme="primary"):
                @render.text
                def lbl_kpi_since_baseline(): return t("kpi_since_baseline")
                @render.text
                def kpi_since_baseline():
                    df = filtered_data()
                    fac = input.detail_facility()
                    if df is None or df.empty or not fac: return "—"
                    sub = df[df[FACILITY_COL].astype(str) == str(fac)]
                    return f"{len(sub):,}"
        
            with ui.value_box(showcase=ui.HTML("🗓️"), theme="bg-gradient-blue-cyan"):
                @render.text
                def lbl_kpi_30d(): return t("kpi_30d")
                @render.text
                def kpi_30d():
                    df = filtered_data()
                    fac = input.detail_facility()
                    if df is None or df.empty or not fac: return "—"
                    sub = df[df[FACILITY_COL].astype(str) == str(fac)]
                    cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(days=30)
                    return f"{int((sub[DATE_COL] >= cutoff).sum()):,}"
        
            with ui.value_box(showcase=ui.HTML("🕐"), theme="bg-gradient-purple-pink"):
                @render.text
                def lbl_kpi_7d(): return t("kpi_7d")
                @render.text
                def kpi_7d():
                    df = filtered_data()
                    fac = input.detail_facility()
                    if df is None or df.empty or not fac: return "—"
                    sub = df[df[FACILITY_COL].astype(str) == str(fac)]
                    cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(days=7)
                    return f"{int((sub[DATE_COL] >= cutoff).sum()):,}"

        # ============== Single-Assessment Snapshot ==============
        with ui.card(full_screen=True):
            @render.ui
            def h_snapshot():
                return ui.card_header(t("card_snapshot"))

            @render.ui
            def desc_snapshot():
                return ui.tags.small(t("desc_snapshot"),
                                     class_="text-muted px-3")

            with ui.layout_columns(col_widths=[7, 5]):

                @render_plotly
                def plot_assessment_bars():
                    df = filtered_data()
                    fac = input.detail_facility()
                    idx = input.detail_assessment()
                    if df is None or df.empty or not fac or idx in (None, ""):
                        return go.Figure()
                    sub = (
                        df[df[FACILITY_COL].astype(str) == str(fac)]
                        .dropna(subset=[DATE_COL]).sort_values(DATE_COL)
                        .reset_index(drop=True)
                    )
                    try:
                        i = int(idx); row = sub.iloc[i]
                    except (ValueError, IndexError):
                        return go.Figure()

                    cols = [c for c in COMPONENT_COLS if c in df.columns]
                    scores = row[cols].astype(float).dropna().sort_values()
                    if scores.empty:
                        return go.Figure()

                    c_labels = component_labels()
                    labels = [c_labels.get(c, c) for c in scores.index]
                    bar_colors = []
                    for v in scores.values:
                        if v <= CRITICAL_THRESHOLD: bar_colors.append(COLOR_CRITICAL)
                        elif v < READY_THRESHOLD:   bar_colors.append(COLOR_AT_RISK)
                        else:                       bar_colors.append(COLOR_READY)

                    fig = go.Figure(go.Bar(
                        x=scores.values, y=labels, orientation="h",
                        marker=dict(color=bar_colors, line=dict(color="white", width=1)),
                        text=[f"{v:.0f}" for v in scores.values],
                        textposition="outside",
                        cliponaxis=False,
                        hovertemplate="<b>%{y}</b><br>" + t("col_score")
                                      + ": %{x:.1f}<extra></extra>",
                    ))
                    fig.add_vline(x=CRITICAL_THRESHOLD, line_dash="dash",
                                  line_color=COLOR_CRITICAL,
                                  annotation_text=t("chart_critical_thresh"),
                                  annotation_position="top right",
                                  annotation_font_color=COLOR_CRITICAL)
                    fig.add_vline(x=READY_THRESHOLD, line_dash="dash",
                                  line_color=COLOR_READY,
                                  annotation_text=t("chart_ready_thresh"),
                                  annotation_position="top right",
                                  annotation_font_color=COLOR_READY)

                    total = row.get(SCORE_TOTAL)
                    total_txt = (f" &nbsp;|&nbsp; <b>{t('chart_total_score')}: {float(total):.1f}</b>"
                                 if pd.notna(total) else "")
                    title = (f"<b>{fac}</b> &nbsp;|&nbsp; "
                             f"{t('assessment_n_date', n=i+1, date=row[DATE_COL].date())}"
                             + total_txt)

                    fig.update_layout(
                        title=dict(text=title, font=dict(size=12), x=0.02, xanchor="left"),
                        height=max(450, len(scores) * 32 + 120),
                        margin=dict(l=10, r=20, t=60, b=10),
                        xaxis=dict(title=t("col_score"), range=[0, 110],
                                   gridcolor="#eee"),
                        plot_bgcolor="white",
                    )
                    return fig

                @render.data_frame
                def assessment_table():
                    df = filtered_data()
                    fac = input.detail_facility()
                    idx = input.detail_assessment()
                    c_labels = component_labels()
                    if df is None or df.empty or not fac or idx in (None, ""):
                        return pd.DataFrame()
                    sub = (
                        df[df[FACILITY_COL].astype(str) == str(fac)]
                        .dropna(subset=[DATE_COL]).sort_values(DATE_COL)
                        .reset_index(drop=True)
                    )
                    try:
                        i = int(idx); sel_row = sub.iloc[i]
                    except (ValueError, IndexError):
                        return pd.DataFrame()
                    baseline_row = sub.iloc[0]
                    is_baseline = (i == 0)

                    cols = [c for c in COMPONENT_COLS if c in df.columns]
                    if SCORE_TOTAL in df.columns:
                        cols = cols + [SCORE_TOTAL]

                    records = []
                    for c in cols:
                        score = sel_row[c]; base = baseline_row[c]
                        if pd.notna(score) and pd.notna(base) and not is_baseline:
                            diff_str = f"{float(score) - float(base):+.1f}"
                        else:
                            diff_str = "—"
                        if pd.notna(score):
                            s = float(score)
                            if s <= CRITICAL_THRESHOLD: status = t("status_critical_short")
                            elif s < READY_THRESHOLD:   status = t("status_at_risk_short")
                            else:                       status = t("status_ready_short")
                        else:
                            status = "—"
                        records.append({
                            t("col_component"): (t("label_total_score")
                                                 if c == SCORE_TOTAL
                                                 else c_labels.get(c, c)),
                            t("col_score"): round(float(score), 1) if pd.notna(score) else None,
                            t("col_delta_baseline"): diff_str,
                            t("col_status"): status,
                        })

                    out = pd.DataFrame(records)
                    return render.DataGrid(out, filters=False, height="500px")

        # ----- Diverging Bar: Change Since Baseline -----
        with ui.card(full_screen=True):
            @render.ui
            def h_diverging():
                return ui.card_header(t("card_diverging"))

            @render.ui
            def desc_diverging():
                return ui.tags.small(t("desc_diverging"),
                                     class_="text-muted px-3")

            @render_plotly
            def plot_diverging_delta():
                df = filtered_data()
                fac = input.detail_facility()
                c_labels = component_labels()
                if df is None or df.empty or not fac: return go.Figure()
                sub = df[df[FACILITY_COL].astype(str) == str(fac)].sort_values(DATE_COL)
                if sub.empty or len(sub) < 2:
                    return go.Figure().update_layout(
                        annotations=[dict(
                            text=t("need_2_assess"),
                            showarrow=False, x=0.5, y=0.5,
                            xref="paper", yref="paper",
                            font=dict(size=14, color="gray"))],
                        height=500,
                    )
                cols = [c for c in COMPONENT_COLS if c in df.columns]
                if not cols: return go.Figure()
                first = sub.iloc[0][cols].astype(float)
                last  = sub.iloc[-1][cols].astype(float)
                delta = (last - first).dropna().sort_values()
                if delta.empty: return go.Figure()
                labels = [c_labels.get(c, c) for c in delta.index]
                values = delta.values
                colors = [COLOR_CRITICAL if v < 0 else (COLOR_READY if v > 0 else "#95a5a6")
                          for v in values]
                max_abs = max(abs(values.min()), abs(values.max()), 1)
                pad = max_abs * 0.2
                fig = go.Figure(go.Bar(
                    x=values, y=labels, orientation="h",
                    marker=dict(color=colors, line=dict(color="white", width=1)),
                    text=[f"{v:+.1f}" for v in values], textposition="outside",
                    hovertemplate="<b>%{y}</b><br>Δ %{x:+.1f}<extra></extra>",
                    cliponaxis=False,
                ))
                fig.add_vline(x=0, line_color="#2c3e50", line_width=2)
                fig.add_annotation(
                    x=-max_abs - pad*0.3, y=1.06, xref="x", yref="paper",
                    text=t("regression"), showarrow=False,
                    font=dict(size=11, color=COLOR_CRITICAL, family="Arial Black"),
                    xanchor="left",
                )
                fig.add_annotation(
                    x=max_abs + pad*0.3, y=1.06, xref="x", yref="paper",
                    text=t("improvement"), showarrow=False,
                    font=dict(size=11, color=COLOR_READY, family="Arial Black"),
                    xanchor="right",
                )
                fig.update_layout(
                    margin=dict(l=10, r=10, t=80, b=40),
                    height=max(500, len(labels)*32 + 120),
                    xaxis=dict(title=t("chart_delta_score"),
                               range=[-max_abs-pad, max_abs+pad],
                               zeroline=False, showgrid=True, gridcolor="#eee"),
                    plot_bgcolor="white", showlegend=False,
                )
                return fig
