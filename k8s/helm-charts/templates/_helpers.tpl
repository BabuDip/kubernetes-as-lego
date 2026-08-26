{{/*
helm.sh/chart label value: "<name>-<version>", per
https://helm.sh/docs/chart_best_practices/labels/
*/}}
{{- define "qless-cafe.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" -}}
{{- end -}}

{{/*
Full label set for a resource. Call with a dict containing "app" and
"component" merged onto the root context, e.g.:
  {{- include "qless-cafe.labels" (merge (dict "app" "django" "component" "web") $) | nindent 4 }}
*/}}
{{- define "qless-cafe.labels" -}}
app: {{ .app }}
component: {{ .component }}
helm.sh/chart: {{ include "qless-cafe.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
environment: {{ .Values.environment }}
{{- end -}}

{{/*
Selector labels only — must stay stable across upgrades, so no chart
version/environment here (those belong in metadata.labels, not matchLabels).
Call with a plain dict: {{ include "qless-cafe.selectorLabels" (dict "app" "django" "component" "web") }}
*/}}
{{- define "qless-cafe.selectorLabels" -}}
app: {{ .app }}
component: {{ .component }}
{{- end -}}
