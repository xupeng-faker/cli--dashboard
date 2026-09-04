import { http } from './http'
import type {
  CommandsPayload,
  DashboardQuery,
  EventsPayload,
  FilterOptions,
  OverviewPayload,
  QualityPayload,
  UsersPayload,
} from '@/types/dashboard'

function as_params(query: DashboardQuery, extra?: Record<string, string | number>) {
  return { ...query, ...extra }
}

export function get_overview(query: DashboardQuery) {
  return http.get<OverviewPayload>('/dashboard/overview', { params: as_params(query) }).then((resp) => resp.data)
}

export function get_commands(query: DashboardQuery) {
  return http.get<CommandsPayload>('/dashboard/commands', { params: as_params(query) }).then((resp) => resp.data)
}

export function get_users(query: DashboardQuery) {
  return http.get<UsersPayload>('/dashboard/users', { params: as_params(query) }).then((resp) => resp.data)
}

export function get_quality(query: DashboardQuery) {
  return http.get<QualityPayload>('/dashboard/quality', { params: as_params(query) }).then((resp) => resp.data)
}

export function get_events(query: DashboardQuery, limit: number, offset: number) {
  return http
    .get<EventsPayload>('/dashboard/events', { params: as_params(query, { limit, offset }) })
    .then((resp) => resp.data)
}

export function get_filter_options(query: DashboardQuery) {
  return http.get<FilterOptions>('/dashboard/filters', { params: as_params(query) }).then((resp) => resp.data)
}
