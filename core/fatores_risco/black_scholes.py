import numpy as np
from scipy.stats import norm

def ajustar_taxa(tx, tipo_tx):
    if tipo_tx != 0:
        return 100 * tipo_tx * np.log(1 + tx / (100 * tipo_tx))
    return tx

def bs_price(S, K, t, R, Q, vol, call_put, tipo_tx):
    R = ajustar_taxa(R, tipo_tx)
    Q = ajustar_taxa(Q, tipo_tx)

    a = np.log(S / K)
    B = ((R / 100) - (Q / 100) + 0.5 * (vol / 100) ** 2) * t
    c = (vol / 100) * np.sqrt(t)
    d1 = (a + B) / c
    d2 = d1 - c

    if call_put == 1:
        return S * np.exp(-(Q / 100) * t) * norm.cdf(d1) - K * np.exp(-(R / 100) * t) * norm.cdf(d2)
    elif call_put == -1:
        return K * np.exp(-(R / 100) * t) * norm.cdf(-d2) - S * np.exp(-(Q / 100) * t) * norm.cdf(-d1)
    else:
        raise ValueError("Valores inválidos.")

def bs_delta(S, K, t, R, Q, vol, call_put, tipo_tx):
    R = ajustar_taxa(R, tipo_tx)
    Q = ajustar_taxa(Q, tipo_tx)

    a = np.log(S / K)
    B = ((R / 100) - (Q / 100) + 0.5 * (vol / 100) ** 2) * t
    c = (vol / 100) * np.sqrt(t)
    d1 = (a + B) / c

    if call_put == 1:
        return np.exp(-(Q / 100) * t) * norm.cdf(d1)
    elif call_put == -1:
        return -np.exp(-(Q / 100) * t) * norm.cdf(-d1)
    else:
        raise ValueError("Valores inválidos.")

def bs_vega(S, K, t, R, Q, vol, call_put, tipo_tx):
    R = ajustar_taxa(R, tipo_tx)
    Q = ajustar_taxa(Q, tipo_tx)

    a = np.log(S / K)
    B = ((R / 100) - (Q / 100) + 0.5 * (vol / 100) ** 2) * t
    c = (vol / 100) * np.sqrt(t)
    d1 = (a + B) / c

    if call_put in [1, -1]:
        return S * np.sqrt(t) * norm.pdf(d1) * np.exp(-(Q / 100) * t)
    else:
        raise ValueError("Valores inválidos.")

def bs_implied_vol(S, K, t, R, Q, price, call_put, tipo_tx, tol=1e-9, max_iter=1000):
    vol_left = 1
    vol_right = 100

    def f(vol):
        return price - bs_price(S, K, t, R, Q, vol, call_put, tipo_tx)

    q_left = f(vol_left)
    q_right = f(vol_right)

    if q_left * q_right > 0:
        return 9999999

    for _ in range(50):
        vol_mid = vol_left + (vol_right - vol_left) * abs(q_left) / (abs(q_left) + abs(q_right))
        q_mid = f(vol_mid)

        if q_mid == 0:
            return vol_mid
        if q_mid * q_left > 0:
            vol_left, q_left = vol_mid, q_mid
        else:
            vol_right, q_right = vol_mid, q_mid

        if abs(vol_right - vol_left) < tol:
            return (vol_left + vol_right) / 2

    # Refina com bisseção
    vol_left, vol_right = 0.001, 100
    for _ in range(max_iter):
        vol_mid = (vol_right + vol_left) / 2
        q_mid = f(vol_mid)

        if q_mid > 0:
            vol_left = vol_mid
        else:
            vol_right = vol_mid

        new_mid = (vol_right + vol_left) / 2
        if abs((new_mid - vol_mid) / new_mid) < tol:
            return new_mid

    return 9999999