provider "google" {
  project = "boonli-menu"
  region  = var.region
}

locals {
  domain_name = "api.boonli.${data.google_dns_managed_zone.dns_zone.dns_name}"
}

resource "google_compute_global_address" "default" {
  name = "${var.project_name}-ip"
}

resource "google_compute_region_network_endpoint_group" "default" {
  name                  = "${var.project_name}-neg"
  network_endpoint_type = "SERVERLESS"
  cloud_run {
    service = var.function_name
  }
  region = var.region
}

resource "google_compute_backend_service" "default" {
  name                  = "${var.project_name}-backend"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  backend {
    group = google_compute_region_network_endpoint_group.default.id
  }
  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

resource "google_compute_url_map" "default" {
  name            = "${var.project_name}-urlmap"
  default_service = google_compute_backend_service.default.id
}

resource "google_compute_target_https_proxy" "default" {
  name             = "${var.project_name}-https-proxy"
  url_map          = google_compute_url_map.default.id
  ssl_certificates = [google_compute_managed_ssl_certificate.default.id]
}

resource "google_compute_global_forwarding_rule" "default" {
  name                  = "${var.project_name}-forwarding-rule"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  ip_address            = google_compute_global_address.default.id
  target                = google_compute_target_https_proxy.default.id
  port_range            = "443"
}

resource "google_compute_managed_ssl_certificate" "default" {
  name = "${var.project_name}-certificate"
  managed {
    domains = [local.domain_name]
  }
}

resource "google_dns_record_set" "default" {
  name = local.domain_name
  type = "A"
  ttl  = 300

  managed_zone = data.google_dns_managed_zone.dns_zone.name

  rrdatas = [google_compute_global_address.default.address]
}

data "google_dns_managed_zone" "dns_zone" {
  name = var.dns_zone
}
