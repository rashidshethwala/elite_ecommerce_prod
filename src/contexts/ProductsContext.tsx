// src/contexts/ProductsContext.tsx
import React, { createContext, useContext } from "react";
import { useProducts } from "../hooks/useProducts";
import { Product, FilterState } from "../types";
import { SortOption } from "../types";  // 👈 import your type

interface ProductsContextValue {
    products: Product[];
    filteredCount: number;
    totalPages: number;
    currentPage: number;
    setCurrentPage: (page: number) => void;
    filters: FilterState;
    updateFilters: (filters: Partial<FilterState>) => void;
    sortOptions: SortOption[];
    loading: boolean;
}

const ProductsContext = createContext<ProductsContextValue | undefined>(
    undefined
);


export const ProductsProvider = ({ children }: { children: React.ReactNode }) => {
    const productsState = useProducts(); // fetch happens once here
    return (
        <ProductsContext.Provider value={productsState}>
            {children}
        </ProductsContext.Provider>
    );
};

export const useProductsContext = () => {
    const context = useContext(ProductsContext);
    if (!context) {
        throw new Error("useProductsContext must be used within ProductsProvider");
    }
    return context;
};
