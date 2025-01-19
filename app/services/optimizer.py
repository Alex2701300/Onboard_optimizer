class LoadingOptimizer:
  def __init__(self):
      self.name = "Loading Optimizer Service"

  async def health_check(self):
      return {"status": "healthy", "service": self.name}