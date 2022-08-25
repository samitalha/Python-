from math import asin, sqrt, cos, sin, atan2, acos, pi, radians, degrees

# Earth radius in meters (https://rechneronline.de/earth-radius/)
E_RADIUS = 6367 * 1000


def step_0(r_e, h_u, h_s, h_a, d_ua, d_sa):
    # Return angular distance between each station U/S and aircraft
    # Triangle UCA and SCA: The three sides are known,

    a = (d_ua - h_a + h_u) * (d_ua + h_a - h_u)
    b = (r_e + h_u) * (r_e + h_a)
    theta_ua = 2 * asin(.5 * sqrt(a / b))

    a = (d_sa - h_a + h_s) * (d_sa + h_a - h_s)
    b = (r_e + h_s) * (r_e + h_a)
    theta_sa = 2 * asin(.5 * sqrt(a / b))

    # Return angular distances between stations and aircraft
    return theta_ua, theta_sa


def step_1(lat_u, lon_u, lat_s, lon_s):
    # Determine angular distance between the two stations
    # and the relative azimuth of one to the other.

    a = sin(.5 * (lat_s - lat_u))
    b = sin(.5 * (lon_s - lon_u))
    c = sqrt(a * a + cos(lat_s) * cos(lat_u) * b * b)
    theta_us = 2 * asin(c)

    a = lon_s - lon_u
    b = cos(lat_s) * sin(a)
    c = sin(lat_s) * cos(lat_u)
    d = cos(lat_s) * sin(lat_u) * cos(a)
    psi_su = atan2(b, c - d)

    return theta_us, psi_su


def step_2(theta_us, theta_ua, theta_sa):
    # Determine whether DME spheres intersect

    if (theta_ua + theta_sa) < theta_us:
        # Spheres are too remote to intersect
        return False

    if abs(theta_ua - theta_sa) > theta_us:
        # Spheres are concentric and don't intersect
        return False

    # Spheres intersect
    return True


def step_3(theta_us, theta_ua, theta_sa):
    # Determine one angle of the USA triangle

    a = cos(theta_sa) - cos(theta_us) * cos(theta_ua)
    b = sin(theta_us) * sin(theta_ua)
    beta_u = acos(a / b)

    return beta_u


def step_4(ac_south, lat_u, lon_u, beta_u, psi_su, theta_ua):
    # Determine aircraft coordinates

    psi_au = psi_su
    if ac_south:
        psi_au += beta_u
    else:
        psi_au -= beta_u

    # Determine aircraft latitude
    a = sin(lat_u) * cos(theta_ua)
    b = cos(lat_u) * sin(theta_ua) * cos(psi_au)
    lat_a = asin(a + b)

    # Determine aircraft longitude
    a = sin(psi_au) * sin(theta_ua)
    b = cos(lat_u) * cos(theta_ua)
    c = sin(lat_u) * sin(theta_ua) * cos(psi_au)
    lon_a = atan2(a, b - c) + lon_u

    return lat_a, lon_a


def main():
    # Program entry point
    # -------------------

    # For this test, I'm using three locations in France:
    # VOR Caen, VOR Evreux and VOR L'Aigle.
    # The angles and horizontal distances between them are known
    # by looking at the low-altitude enroute chart which I've posted
    # here: https://i.stack.imgur.com/m8Wmw.png
    # We know there coordinates and altitude by looking at the AIP France too.
    # For DMS <--> Decimal degrees, this tool is handy:
    # https://www.rapidtables.com/convert/number/degrees-minutes-seconds-to-degrees.html

    # Let's pretend the aircraft is at LGL
    # lat = 48.79061, lon = 0.5302778

    # Stations U and S are:
    u = {'label': 'PORT', 'lat': 33.560043287809236,  'lon': 72.8331113998903, 'alt': 82}
    s = {'label': 'ISB', 'lat': 32.597280556783176,  'lon': 74.0821311931787, 'alt': 152}

    # We know the aircraft altitude
    a_alt = 3000  # meters

    # We know the approximate slant ranges to stations U and S
    au_range = 54272.94033414796
    as_range = 104785.2782452054

    # Compute angles station - earth center - aircraft for U and S
    # Expected values UA: 0.0130890288 rad
    #                 SA: 0.0090168045 rad
    theta_ua, theta_sa = step_0(
        r_e=E_RADIUS,  # Earth
        h_u=u['alt'],  # Station U altitude
        h_s=s['alt'],  # Station S altitude
        h_a=a_alt, d_ua=au_range, d_sa=as_range  # aircraft data
    )

    # Compute angle between station, and their relative azimuth
    # We need to convert angles into radians
    theta_us, psi_su = step_1(
        lat_u=radians(u['lat']), lon_u=radians(u['lon']),  # Station U coordinates
        lat_s=radians(s['lat']), lon_s=radians(s['lon']))   # Station S coordinates

    # Check validity of ranges
    if not step_2(
            theta_us=theta_us,
            theta_ua=theta_ua,
            theta_sa=theta_sa):
        # Cannot compute, spheres don't intersect
        print('Cannot compute, ranges are not consistant')
        return 1

    # Solve one angle of the USA triangle
    beta_u = step_3(
        theta_us=theta_us,
        theta_ua=theta_ua,
        theta_sa=theta_sa)

    # Compute aircraft coordinates.
    # The first parameter is whether the aircraft is south of the line
    # between U and S. If you don't know, then you need to compute
    # both, once with ac_south = False, once with ac_south = True.
    # You will get the two possible positions, one must be eliminated.

    # North position
    lat_n, lon_n = step_4(
        ac_south=False,  # See comment above
        lat_u=radians(u['lat']), lon_u=radians(u['lon']),  # Station U
        beta_u=beta_u, psi_su=psi_su, theta_ua=theta_ua  # previously computed
    )
    pn = {'label': 'P north', 'lat': degrees(lat_n), 'lon': degrees(lon_n), 'alt': a_alt}

    # South position
    lat_s, lon_s = step_4(
        ac_south=True,
        lat_u=radians(u['lat']), lon_u=radians(u['lon']),
        beta_u=beta_u, psi_su=psi_su, theta_ua=theta_ua)
    ps = {'label': 'P south', 'lat': degrees(lat_s), 'lon': degrees(lon_s), 'alt': a_alt}

    # Print results
    fmt = '{}: lat {}, lon {}, alt {}'
    for p in u, s, pn, ps:
        print(fmt.format(p['label'], p['lat'], p['lon'], p['alt']))

    # The expected result is about:
    #   CAN: lat 49.17319, lon -0.4552778, alt 82
    #   EVX: lat 49.03169, lon 1.220861, alt 152
    #   P north: lat ??????, lon ??????, alt 296
    #   P south: lat 48.79061, lon 0.5302778, alt 296
    if __name__ == '__main__':
     main()
