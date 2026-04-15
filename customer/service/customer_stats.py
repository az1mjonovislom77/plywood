from customer.selectors.customer_selectors import CustomerStatsSelector


class CustomerStatsService:

    @staticmethod
    def dashboard():
        return CustomerStatsSelector.dashboard_stats()
