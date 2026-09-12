from .evaluator import select_best

def select_model(community, target_variable, metrics):
    selected = select_best(metrics)
    return {"community": community.id, "target_variable": target_variable, "selected_model": selected, "reason": "Lowest validation MAE, with RMSE as tie-breaker", "metrics": metrics}
