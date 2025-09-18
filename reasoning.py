def reason_for_pick(player, market, line, model_mean, model_edge, context):
    bullets=[]
    if "tgt_share" in context: bullets.append(f"Target share last 4W: {context['tgt_share']:.1%}")
    if "adot" in context: bullets.append(f"aDOT last 4W: {context['adot']:.1f}")
    if "epa_pass_off" in context and "epa_pass_def" in context:
        bullets.append(f"Off EPA/pass {context['epa_pass_off']:+.2f} vs opp Def EPA/pass {context['epa_pass_def']:+.2f}")
    if "wind" in context: bullets.append(f"Wind ~{context['wind']} mph")
    if "pace" in context: bullets.append(f"Neutral pace ~{context['pace']:.1f} s/play")
    s = f"{player} — {market} {line}\nModel mean: {model_mean:.1f} | Edge: {model_edge:+.2%}\n" + "\n".join(f"- {b}" for b in bullets)
    return s
