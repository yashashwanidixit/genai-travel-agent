"""Provider abstractions for external/mock data sources.

Downstream code (search orchestration, future recommendation) should
depend on the HotelProvider interface, never on a concrete
implementation like MockHotelProvider directly.
"""