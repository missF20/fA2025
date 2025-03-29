import { useState, useCallback } from 'react';
import { z } from 'zod';
import { log } from '../utils/logger';

interface UseFormOptions<T> {
  initialValues: T;
  validationSchema: z.ZodSchema<T>;
  onSubmit: (values: T) => Promise<void>;
}

interface FormState<T> {
  values: T;
  errors: Partial<Record<keyof T, string>>;
  touched: Partial<Record<keyof T, boolean>>;
}

export function useForm<T extends Record<string, any>>({
  initialValues,
  validationSchema,
  onSubmit,
}: UseFormOptions<T>) {
  const [formState, setFormState] = useState<FormState<T>>({
    values: initialValues,
    errors: {},
    touched: {},
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateField = useCallback(
    (name: keyof T, value: any) => {
      try {
        validationSchema.shape[name].parse(value);
        return '';
      } catch (error) {
        if (error instanceof z.ZodError) {
          return error.errors[0].message;
        }
        return 'Invalid value';
      }
    },
    [validationSchema]
  );

  const handleChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const { name, value, type, checked } = event.target;
      const newValue = type === 'checkbox' ? checked : value;

      setFormState((prev) => ({
        ...prev,
        values: { ...prev.values, [name]: newValue },
        errors: {
          ...prev.errors,
          [name]: validateField(name as keyof T, newValue),
        },
      }));
    },
    [validateField]
  );

  const handleBlur = useCallback((event: React.FocusEvent<HTMLInputElement>) => {
    const { name } = event.target;
    setFormState((prev) => ({
      ...prev,
      touched: { ...prev.touched, [name]: true },
    }));
  }, []);

  const handleSubmit = useCallback(
    async (event: React.FormEvent) => {
      event.preventDefault();
      setIsSubmitting(true);

      try {
        const validatedData = validationSchema.parse(formState.values);
        await onSubmit(validatedData);
        setFormState((prev) => ({
          ...prev,
          errors: {},
          touched: {},
        }));
      } catch (error) {
        if (error instanceof z.ZodError) {
          const errors = error.errors.reduce((acc, curr) => {
            const path = curr.path[0] as keyof T;
            acc[path] = curr.message;
            return acc;
          }, {} as Record<keyof T, string>);

          setFormState((prev) => ({
            ...prev,
            errors,
            touched: Object.keys(prev.values).reduce((acc, key) => {
              acc[key] = true;
              return acc;
            }, {} as Record<string, boolean>),
          }));
        } else {
          log.error('Form validation error:', error);
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [formState.values, validationSchema, onSubmit]
  );

  const reset = useCallback(() => {
    setFormState({
      values: initialValues,
      errors: {},
      touched: {},
    });
  }, [initialValues]);

  return {
    values: formState.values,
    errors: formState.errors,
    touched: formState.touched,
    isSubmitting,
    handleChange,
    handleBlur,
    handleSubmit,
    reset,
  };
}