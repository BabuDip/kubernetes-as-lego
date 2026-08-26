{{/*
helm.sh/chart label value: "<name>-<version>", per
https://helm.sh/docs/chart_best_practices/labels/
*/}}
{{- define "qless-cafe.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" -}}
{{- end -}}

{{/*
Release-scoped name prefix for every resource, e.g. "myrelease-qless-cafe" —
suffix with "-<component>" (e.g. "<fullname>-django") when naming a resource.
Without this, resource names are fixed strings ("django", "postgres", ...)
and a second release in the same namespace fails on name collisions.
https://helm.sh/docs/chart_best_practices/naming/
*/}}
{{- define "qless-cafe.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
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
Includes the release name so two releases in the same namespace never select
each other's pods. Call with "app"/"component" merged onto the root context:
  {{- include "qless-cafe.selectorLabels" (merge (dict "app" "django" "component" "web") $) }}
*/}}
{{- define "qless-cafe.selectorLabels" -}}
app: {{ .app }}
component: {{ .component }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
