"""Provider adapters for recon-hub."""

from .base import Provider
from .certspotter import CertSpotterProvider
from .crtsh import CrtshProvider
from .extra import (
    AbuseIPDBProvider,
    CensysProvider,
    GreyNoiseProvider,
    HunterProvider,
    IPinfoProvider,
    NetlasProvider,
    QuakeProvider,
    SecurityTrailsProvider,
    ShodanProvider,
    VirusTotalProvider,
    ZoomEyeProvider,
)
from .otx import OtxProvider
from .urlscan import UrlscanProvider
from .wayback import WaybackProvider

_PROVIDERS: dict[str, Provider] = {
    CrtshProvider.name: CrtshProvider(),
    CertSpotterProvider.name: CertSpotterProvider(),
    UrlscanProvider.name: UrlscanProvider(),
    OtxProvider.name: OtxProvider(),
    WaybackProvider.name: WaybackProvider(),
    ShodanProvider.name: ShodanProvider(),
    CensysProvider.name: CensysProvider(),
    QuakeProvider.name: QuakeProvider(),
    ZoomEyeProvider.name: ZoomEyeProvider(),
    HunterProvider.name: HunterProvider(),
    NetlasProvider.name: NetlasProvider(),
    VirusTotalProvider.name: VirusTotalProvider(),
    SecurityTrailsProvider.name: SecurityTrailsProvider(),
    GreyNoiseProvider.name: GreyNoiseProvider(),
    AbuseIPDBProvider.name: AbuseIPDBProvider(),
    IPinfoProvider.name: IPinfoProvider(),
}


def get_provider(name: str) -> Provider | None:
    return _PROVIDERS.get(name)


def list_providers() -> list[str]:
    return sorted(_PROVIDERS.keys())
