def dispatch_energy(demand, solar_available, wind_available, battery_percent, battery_minimum, diesel_price, forecast_solar=None, forecast_wind=None, forecast_demand=None, battery_capacity_kw=None):
    demand = max(float(forecast_demand if forecast_demand is not None else demand), 0)
    solar = min(demand, max(float(solar_available), 0))
    wind = min(max(demand - solar, 0), max(float(wind_available), 0))
    remaining = max(demand - solar - wind, 0)
    battery = min(remaining, battery_capacity_kw or remaining) if battery_percent > battery_minimum else 0
    diesel = min(max(remaining - battery, 0), max(demand, 0))
    renewable_share = ((solar + wind + battery) / demand * 100) if demand else 100
    cost = diesel * 0.28 * diesel_price
    co2 = diesel * 0.72
    forecast_change = (float(forecast_solar) - float(solar_available)) if forecast_solar is not None else 0
    renewable_meets_demand = solar + wind >= demand
    recommendation = "Hold diesel in reserve while renewables meet demand." if renewable_meets_demand and diesel == 0 else ("Charge battery now before the forecast renewable dip." if forecast_solar is not None and forecast_change < 0 and battery_percent > battery_minimum else ("Hold diesel in reserve while renewables meet demand." if diesel == 0 else "Diesel support is required to protect reliability at current demand."))
    return {"solar_kw": round(solar, 1), "wind_kw": round(wind, 1), "battery_kw": round(battery, 1), "diesel_kw": round(diesel, 1), "renewable_share": round(renewable_share), "cost_per_hour": round(cost, 2), "co2_kg_per_hour": round(co2, 2), "recommendation": recommendation}
