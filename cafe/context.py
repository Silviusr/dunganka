def cart_summary(request):
    return {"cart_count": sum(request.session.get("cart", {}).values())}
