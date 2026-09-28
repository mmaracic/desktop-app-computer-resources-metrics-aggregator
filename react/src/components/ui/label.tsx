import * as React from "react"
import { cn } from "../../lib/utils"

const Label = React.forwardRef<
    HTMLLabelElement,
    React.LabelHTMLAttributes<HTMLLabelElement>
>(({ className, ...props }, ref) => {
    const id = React.useId()

    return (
        <label
            ref={ref}
            htmlFor={id}
            className={cn(
                "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
                className
            )}
            {...props}
        />
    )
})
Label.displayName = "Label"

export { Label }
