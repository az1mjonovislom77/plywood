from supplier.selectors.supplier_selectors import SupplierSelector


class SupplierStatsService:

    @staticmethod
    def get_debt_stats():
        return SupplierSelector.debt_stats()


def get_supplier_transactions_with_stats(supplier_id):
    return SupplierSelector.transactions_with_stats(supplier_id)
