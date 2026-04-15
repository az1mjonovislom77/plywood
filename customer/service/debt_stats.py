from customer.selectors.customer_selectors import CustomerDebtSelector


class DashboardStatsService:

    @staticmethod
    def get_debt_stats():
        return CustomerDebtSelector.dashboard_debt_stats()
